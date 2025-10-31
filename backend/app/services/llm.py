import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx


log = logging.getLogger(__name__)


class LLMService:
    """Client helper for OpenAI-compatible chat endpoints."""

    def __init__(
        self,
        base_url: str,
        default_model: Optional[str] = None,
        request_timeout: Optional[float] = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.request_timeout = request_timeout

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Execute a standard (non-streaming) chat completion request."""

        payload: Dict[str, Any] = {
            "messages": messages,
        }
        chosen_model = model or self.default_model
        if chosen_model is not None:
            payload["model"] = chosen_model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{self.base_url}/chat/completions"
        log.debug("POST %s payload=%s", url, payload)

        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            response = await client.post(url, json=payload)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            log.error("LLM error response %s: %s", exc.response.status_code, exc.response.text)
            raise RuntimeError(
                f"LLM request failed with status {exc.response.status_code}"
            ) from exc

        parsed = response.json()
        choice = (parsed.get("choices") or [{}])[0]
        content = ((choice.get("message") or {}).get("content")) or ""
        return content, parsed

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[bytes]:
        """Stream chat completion events from the upstream LLM server."""

        payload: Dict[str, Any] = {
            "messages": messages,
            "stream": True,
        }
        chosen_model = model or self.default_model
        if chosen_model is not None:
            payload["model"] = chosen_model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{self.base_url}/chat/completions"
        log.debug("STREAM %s payload=%s", url, payload)

        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            formatted = f"data: {line}"
                        else:
                            formatted = line
                        if not formatted.endswith("\n\n"):
                            formatted = f"{formatted}\n\n"
                        yield formatted.encode("utf-8")
            except httpx.HTTPStatusError as exc:
                text = exc.response.text[:500]
                log.error(
                    "LLM streaming request failed: status=%s body=%s",
                    exc.response.status_code,
                    text,
                )
                error_payload = json.dumps({"error": text or str(exc)})
                yield f"data: {error_payload}\n\n".encode("utf-8")
                yield "data: [DONE]\n\n".encode("utf-8")
            except Exception as exc:  # pragma: no cover - defensive logging
                log.exception("LLM streaming unexpected failure")
                error_payload = json.dumps({"error": str(exc)})
                yield f"data: {error_payload}\n\n".encode("utf-8")
                yield "data: [DONE]\n\n".encode("utf-8")
