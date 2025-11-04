import json
import logging
from typing import List

from fastapi import APIRouter, Depends

from ...core import settings
from ...schemas.chat import ChatMessage
from ...schemas.dictionary import DictionaryRequest, DictionaryResponse
from ...services.llm import LLMService
from ..dependencies import get_llm_service

router = APIRouter(tags=["dictionary"])
log = logging.getLogger(__name__)


def _build_dictionary_messages(word: str, sentence: str) -> List[ChatMessage]:
    """Create chat messages explaining the dictionary request to the LLM."""
    prompt = settings.llm_dictionary_prompt
    payload = json.dumps({"word": word, "sentence": sentence}, ensure_ascii=False)
    return [
        ChatMessage(role="system", content=prompt),
        ChatMessage(role="user", content=payload),
    ]


def _normalize_dictionary_result(payload: str, fallback_word: str) -> DictionaryResponse:
    """Coerce raw LLM output into the structured DictionaryResponse model."""
    stripped = payload.strip()
    if not stripped:
        return DictionaryResponse(
            headword=fallback_word,
            part_of_speech=None,
            phonetics=[],
            definition="暫無定義",
            examples=[],
            notes=None,
        )

    if stripped.startswith("```"):
        segments = [segment.strip() for segment in stripped.split("```") if segment.strip()]
        if segments:
            stripped = segments[-1]
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
        return DictionaryResponse(
            headword=fallback_word,
            part_of_speech=None,
            phonetics=[],
            definition=stripped,
            examples=[],
            notes=None,
        )

    if isinstance(data, dict):
        headword = (data.get("headword") or fallback_word).strip() or fallback_word
        part_of_speech = (data.get("part_of_speech") or None) or None
        phonetics_raw = data.get("phonetics")
        if isinstance(phonetics_raw, list):
            phonetics = [str(item).strip() for item in phonetics_raw if str(item).strip()]
        else:
            phonetics = []
        definition = (
            str(data.get("definition") or "\u66ab\u7121\u5b9a\u7fa9").strip()
            or "\u66ab\u7121\u5b9a\u7fa9"
        )
        examples_raw = data.get("examples")
        if isinstance(examples_raw, list):
            examples = [str(item).strip() for item in examples_raw if str(item).strip()]
        elif isinstance(examples_raw, str):
            examples = [examples_raw.strip()] if examples_raw.strip() else []
        else:
            examples = []
        notes_raw = data.get("notes")
        notes = str(notes_raw).strip() if notes_raw is not None else None
        if notes == "":
            notes = None
        return DictionaryResponse(
            headword=headword,
            part_of_speech=part_of_speech,
            phonetics=phonetics,
            definition=definition,
            examples=examples,
            notes=notes,
        )

    return DictionaryResponse(
        headword=fallback_word,
        part_of_speech=None,
        phonetics=[],
        definition=stripped,
        examples=[],
        notes=None,
    )


@router.post("/dictionary", response_model=DictionaryResponse)
async def dictionary_lookup(
    request: DictionaryRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> DictionaryResponse:
    messages = _build_dictionary_messages(request.word, request.sentence)
    model_choice = (
        request.model
        or settings.llm_dictionary_model
        or settings.llm_default_model
    )
    raw: dict | None = None
    try:
        content, raw = await llm_service.chat(
            messages=[m.model_dump() for m in messages],
            model=model_choice,
            temperature=0.0,
        )
    except Exception as exc:  # pragma: no cover - graceful fallback when LLM unavailable
        log.warning("Dictionary lookup failed: %s", exc)
        return DictionaryResponse(
            headword=request.word,
            part_of_speech=None,
            phonetics=[],
            definition="目前無法取得字典資料，請稍後再試。",
            examples=[],
            notes=None,
            model=None,
        )

    normalized = _normalize_dictionary_result(content, fallback_word=request.word)
    metadata = raw or {}
    payload = normalized.model_dump()
    payload["model"] = metadata.get("model") or payload.get("model")
    return DictionaryResponse(**payload)

