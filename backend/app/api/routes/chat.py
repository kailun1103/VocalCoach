import asyncio
import json
import logging
import re
from typing import List, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...core import settings
from ...schemas.chat import ChatMessage, ChatRequest, ChatResponse
from ...services.llm import LLMService
from ..dependencies import get_llm_service

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

_FORBIDDEN_CHARS: frozenset[str] = frozenset(
    {
        '#',
        '*',
        '/',
        '%',
        '-',
        '"',
        "'",
        '`',
        '•',  # bullet
        '●',  # black circle
        '▪',  # black small square
        '‧',  # hyphenation point
        '·',  # middle dot
        '“',  # left double quotation mark
        '”',  # right double quotation mark
        '‘',  # left single quotation mark
        '’',  # right single quotation mark
        '–',  # en dash
        '—',  # em dash
        '\n',
        '\r',
        '\t',
    }
)
_WORD_PATTERN = re.compile(r"[A-Za-z]+")


def _with_system_prompt(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Prepend default system prompt when none is supplied."""
    prompt = settings.llm_system_prompt
    if not prompt:
        return list(messages)
    for message in messages:
        if message.role == "system":
            return list(messages)
    return [ChatMessage(role="system", content=prompt), *messages]


def _normalize_whitespace(text: str) -> str:
    """Collapse consecutive whitespace into single spaces."""
    return " ".join(text.strip().split())


def _strip_forbidden(text: str) -> str:
    """Remove symbols that break TTS output or violate classroom rules."""
    return "".join(ch for ch in text if ch not in _FORBIDDEN_CHARS)


def _count_words(text: str) -> int:
    """Count English words using a conservative regex."""
    return len(_WORD_PATTERN.findall(text))


def _validate_response(content: str) -> Tuple[bool, str]:
    """Check whether an LLM reply satisfies symbol and word-count requirements."""
    if not content.strip():
        return False, "the response was empty"
    if any(ch in _FORBIDDEN_CHARS for ch in content):
        return False, "the response used forbidden symbols or line breaks"
    normalized = _normalize_whitespace(content)
    word_total = _count_words(normalized)
    if word_total < settings.llm_response_word_min:
        return False, f"the response only used {word_total} words"
    if word_total > settings.llm_response_word_max:
        return False, f"the response used {word_total} words"
    return True, ""


def _build_retry_instruction(reason: str) -> str:
    """Explain the failure reason and restate the formatting rules."""
    return (
        "Rewrite your previous answer now so it follows every rule: respond in two or three sentences, "
        "use a total of five to fifteen English words, avoid quotation marks, emoji, special symbols "
        "(# * / % -), apostrophes, and bullet lists, and keep commas natural. You failed because "
        f"{reason}. Produce a corrected answer immediately."
    )


def _apply_fallback(original: str) -> str:
    """Produce a deterministic filler paragraph when the LLM keeps failing."""
    sanitized = _normalize_whitespace(_strip_forbidden(original))
    words = sanitized.split()
    if not words:
        words = [
            "I", "will", "keep", "practising", "clear", "English", "sentences", "each", "day",
            "to", "build", "steady", "confidence", "and", "stay", "calm", "during", "our", "conversation",
        ]
    if len(words) > settings.llm_response_word_max:
        words = words[: settings.llm_response_word_max]
    filler = (
        "I focus on calm pacing and thoughtful ideas while expressing myself and encouraging patient progress every day"
    ).split()
    while len(words) < settings.llm_response_word_min:
        for token in filler:
            if len(words) >= settings.llm_response_word_max:
                break
            words.append(token)
        if len(words) >= settings.llm_response_word_min:
            break
    fallback = " ".join(words[: settings.llm_response_word_max])
    if not fallback.endswith((".", "!", "?")):
        fallback += "."
    return fallback


async def _generate_response_with_constraints(
    messages: List[ChatMessage],
    llm_service: LLMService,
    model: str | None,
    temperature: float | None,
    max_tokens: int | None,
) -> Tuple[str, dict]:
    """Call the LLM and enforce hard output constraints with retries and trimming."""
    attempt_messages = list(messages)
    chosen_temperature = temperature if temperature is not None else settings.llm_default_temperature
    last_raw: dict = {}
    for attempt in range(settings.llm_response_retry_attempts + 1):
        content, last_raw = await llm_service.chat(
            messages=[m.model_dump() for m in attempt_messages],
            model=model,
            temperature=chosen_temperature,
            max_tokens=max_tokens,
        )
        is_valid, reason = _validate_response(content)
        normalized = _normalize_whitespace(content)
        if is_valid:
            sanitized = _normalize_whitespace(_strip_forbidden(normalized))
            return sanitized, last_raw

        log.warning(
            "LLM response violated constraints (attempt %s/%s): %s",
            attempt + 1,
            settings.llm_response_retry_attempts + 1,
            reason,
        )
        if attempt >= settings.llm_response_retry_attempts:
            break
        attempt_messages = [
            *attempt_messages,
            ChatMessage(role="assistant", content=normalized),
            ChatMessage(role="user", content=_build_retry_instruction(reason)),
        ]

    fallback = _apply_fallback(content if "content" in locals() else "")
    log.warning("Returning fallback response after exhausting retries.")
    return fallback, last_raw


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """Proxy chat to local OpenAI-compatible LLM server (e.g., LM Studio/Ollama)."""
    prepared_messages = _with_system_prompt(request.messages)
    content, raw = await _generate_response_with_constraints(
        messages=prepared_messages,
        llm_service=llm_service,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    usage = raw.get("usage") or {}
    choice0 = (raw.get("choices") or [{}])[0]
    return ChatResponse(
        content=content,
        model=raw.get("model"),
        finish_reason=choice0.get("finish_reason"),
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )


@router.post("/chat/stream", response_class=StreamingResponse)
async def chat_stream(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """Stream chat completions via Server-Sent Events."""
    prepared_messages = _with_system_prompt(request.messages)
    content, raw = await _generate_response_with_constraints(
        messages=prepared_messages,
        llm_service=llm_service,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    payload = {"choices": [{"delta": {"content": content}}], "model": raw.get("model")}

    async def event_generator():
        try:
            yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"
        except asyncio.CancelledError:
            log.debug("Client closed chat stream early")
            raise

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
