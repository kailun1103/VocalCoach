import json
from typing import List, Tuple

from fastapi import APIRouter, Depends

from ...core import settings
from ...schemas.chat import ChatMessage
from ...schemas.grammar import GrammarCheckRequest, GrammarCheckResponse
from ...services.llm import LLMService
from ..dependencies import get_llm_service

router = APIRouter(tags=["grammar"])


def _build_grammar_messages(text: str) -> List[ChatMessage]:
    """Construct chat messages for grammar checking."""
    prompt = settings.llm_grammar_prompt
    return [
        ChatMessage(role="system", content=prompt),
        ChatMessage(role="user", content=text),
    ]


def _normalize_grammar_result(raw: str) -> Tuple[bool, str, str | None]:
    """Attempt to coerce the LLM response into structured grammar feedback."""
    stripped = raw.strip()
    if not stripped:
        return False, "No grammar feedback returned. Please try again.", None

    # Remove common code fences and language hints (e.g. ```json ... ```).
    if stripped.startswith("```"):
        segments = [segment.strip() for segment in stripped.split("```") if segment.strip()]
        if segments:
            stripped = segments[0]
    if stripped.lower().startswith("json"):
        stripped = stripped[4:].strip()

    if stripped and not stripped.lstrip().startswith("{"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and start < end:
            stripped = stripped[start : end + 1]

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return False, stripped, None

    if isinstance(data, dict):
        is_correct = bool(data.get("is_correct"))
        feedback = str(data.get("feedback") or "").strip()
        suggestion_raw = data.get("suggestion")
        suggestion = str(suggestion_raw).strip() if suggestion_raw is not None else None
        if not feedback:
            feedback = "Grammar check completed."
        if suggestion == "":
            suggestion = None
        return is_correct, feedback, suggestion

    return False, stripped, None


@router.post("/grammar", response_model=GrammarCheckResponse)
async def grammar_check(
    request: GrammarCheckRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> GrammarCheckResponse:
    """Analyse user text and report grammar issues using the configured LLM."""
    messages = _build_grammar_messages(request.text)
    model_choice = (
        request.model
        or settings.llm_grammar_model
        or settings.llm_default_model
    )
    content, raw = await llm_service.chat(
        messages=[m.model_dump() for m in messages],
        model=model_choice,
        temperature=0.0,
    )
    is_correct, feedback, suggestion = _normalize_grammar_result(content)
    return GrammarCheckResponse(
        is_correct=is_correct,
        feedback=feedback,
        suggestion=suggestion,
        model=raw.get("model"),
    )
