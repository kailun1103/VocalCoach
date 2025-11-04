"""Pydantic schemas used across API endpoints."""

from .chat import ChatMessage, ChatRequest, ChatResponse
from .dictionary import DictionaryRequest, DictionaryResponse
from .grammar import GrammarCheckRequest, GrammarCheckResponse
from .speech import TextToSpeechRequest, TextToSpeechResponse, TranscriptionResponse
from .translation import TranslationRequest, TranslationResponse

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "DictionaryRequest",
    "DictionaryResponse",
    "GrammarCheckRequest",
    "GrammarCheckResponse",
    "TextToSpeechRequest",
    "TextToSpeechResponse",
    "TranscriptionResponse",
    "TranslationRequest",
    "TranslationResponse",
]
