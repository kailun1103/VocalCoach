from typing import List

from fastapi import APIRouter, Depends

from ...core import settings
from ...schemas.chat import ChatMessage
from ...schemas.translation import TranslationRequest, TranslationResponse
from ...services.llm import LLMService
from ..dependencies import get_llm_service

router = APIRouter(tags=["translation"])


def _build_translation_messages(text: str, target_language: str) -> List[ChatMessage]:
    """Construct messages for translation requests."""
    prompt_template = settings.llm_translation_prompt
    try:
        system_prompt = prompt_template.format(target_language=target_language)
    except (KeyError, IndexError, ValueError):
        system_prompt = prompt_template
    return [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=text),
    ]


@router.post("/translate", response_model=TranslationResponse)
async def translate(
    request: TranslationRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> TranslationResponse:
    """Translate text into a target language using the configured LLM."""
    target_language = (request.target_language or "zh-TW").strip() or "zh-TW"
    messages = _build_translation_messages(request.text, target_language)
    model_choice = (
        request.model
        or settings.llm_translation_model
        or settings.llm_default_model
    )
    content, raw = await llm_service.chat(
        messages=[m.model_dump() for m in messages],
        model=model_choice,
        temperature=0.0,
    )
    return TranslationResponse(
        translated_text=content.strip(),
        model=raw.get("model"),
    )
