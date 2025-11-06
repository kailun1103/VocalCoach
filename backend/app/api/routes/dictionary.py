"""
字典查詢 API 路由模組

此模組提供單字查詢功能，透過 LLM 返回包含定義、例句、
發音和學習提示的完整字典資訊。
"""

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


def _build_dictionary_messages(word: str) -> List[ChatMessage]:
    """
    建立字典查詢的聊天訊息
    
    參數:
        word: 要查詢的目標單字
    
    返回:
        List[ChatMessage]: 包含系統提示和使用者查詢的訊息列表
    
    說明:
        使用 JSON 格式將單字傳遞給 LLM，
        系統提示詞定義了返回的字典格式。
    """
    prompt = settings.llm_dictionary_prompt
    payload = json.dumps({"word": word}, ensure_ascii=False)
    return [
        ChatMessage(role="system", content=prompt),
        ChatMessage(role="user", content=payload),
    ]


def _normalize_dictionary_result(payload: str, fallback_word: str) -> DictionaryResponse:
    """
    標準化 LLM 原始輸出為結構化字典回應
    
    參數:
        payload: LLM 返回的原始文字
        fallback_word: 當解析失敗時使用的備用單字
    
    返回:
        DictionaryResponse: 結構化的字典資料
    
    說明:
        嘗試從 LLM 輸出中提取 JSON 資料，處理常見的格式問題，
        如 Markdown 程式碼區塊、多餘的文字等。若解析失敗，
        返回包含原始文字的最小回應。
    """
    stripped = payload.strip()
    
    # 處理空回應
    if not stripped:
        return DictionaryResponse(
            headword=fallback_word,
            part_of_speech=None,
            definition="No definition",
            examples=[],
        )

    # 移除 Markdown 程式碼區塊標記
    if stripped.startswith("```"):
        segments = [segment.strip() for segment in stripped.split("```") if segment.strip()]
        if segments:
            stripped = segments[-1]
    
    # 移除 "json" 前綴
    if stripped.lower().startswith("json"):
        stripped = stripped[4:].strip()
    
    # 提取 JSON 物件（處理多餘的文字）
    if stripped and not stripped.lstrip().startswith("{"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and start < end:
            stripped = stripped[start : end + 1]

    # 嘗試解析 JSON
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        # JSON 解析失敗，返回原始文字作為定義
        return DictionaryResponse(
            headword=fallback_word,
            part_of_speech=None,
            definition=stripped,
            examples=[],
        )

    # 從解析的 JSON 中提取字典欄位
    if isinstance(data, dict):
        # 提取標題詞（headword）
        headword = (data.get("headword") or fallback_word).strip() or fallback_word
        
        # 提取詞性（處理字串或列表格式）
        part_of_speech_raw = data.get("part_of_speech")
        if isinstance(part_of_speech_raw, list):
            # 若是列表，取第一個元素或用逗號連接
            part_of_speech = part_of_speech_raw[0] if part_of_speech_raw else None
        elif isinstance(part_of_speech_raw, str):
            part_of_speech = part_of_speech_raw.strip() or None
        else:
            part_of_speech = None
        
        # 提取定義（必填欄位）
        definition = (
            str(data.get("definition") or "No definition").strip()
            or "No definition"
        )
        
        # 提取例句列表（限制最多 3 個）
        examples_raw = data.get("examples")
        if isinstance(examples_raw, list):
            examples = [str(item).strip() for item in examples_raw if str(item).strip()][:3]
        elif isinstance(examples_raw, str):
            examples = [examples_raw.strip()] if examples_raw.strip() else []
        else:
            examples = []
        
        return DictionaryResponse(
            headword=headword,
            part_of_speech=part_of_speech,
            definition=definition,
            examples=examples,
        )

    # 資料格式不符合預期，返回最小回應
    return DictionaryResponse(
        headword=fallback_word,
        part_of_speech=None,
        definition=stripped,
        examples=[],
    )


@router.post("/dictionary", response_model=DictionaryResponse)
async def dictionary_lookup(
    request: DictionaryRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> DictionaryResponse:
    """
    字典查詢 API 端點
    
    參數:
        request: 包含目標單字和句子上下文的查詢請求
        llm_service: LLM 服務實例（透過依賴注入）
    
    返回:
        DictionaryResponse: 包含單字定義、發音、例句等完整資訊
    
    說明:
        使用 LLM 查詢單字資訊，返回結構化的字典資料。
        若 LLM 服務不可用，返回友善的錯誤訊息。
        temperature 設為 0.0 以確保結果的一致性。
    """
    # 建立 LLM 查詢訊息
    messages = _build_dictionary_messages(request.word)
    
    # 選擇使用的模型（優先級：請求指定 > 字典專用 > 預設）
    model_choice = (
        request.model
        or settings.llm_dictionary_model
        or settings.llm_default_model
    )
    
    # 呼叫 LLM 服務
    raw: dict | None = None
    try:
        content, raw = await llm_service.chat(
            messages=[m.model_dump() for m in messages],
            model=model_choice,
            temperature=0.0,  # 確保輸出的一致性
        )
    except Exception as exc:
        # 優雅降級：LLM 服務不可用時返回錯誤訊息
        log.warning("Dictionary Search failed: %s", exc)
        return DictionaryResponse(
            headword=request.word,
            part_of_speech=None,
            definition="No definition available, please try again later.",
            examples=[],
            model=None,
        )

    # 標準化 LLM 輸出為結構化資料
    normalized = _normalize_dictionary_result(content, fallback_word=request.word)
    
    # 添加模型資訊到回應中
    metadata = raw or {}
    payload = normalized.model_dump()
    payload["model"] = metadata.get("model") or payload.get("model")
    
    return DictionaryResponse(**payload)