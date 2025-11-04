from functools import lru_cache
from pathlib import Path

from ..core import settings
from ..services import STTService, TTSService
from ..services.llm import LLMService


@lru_cache
def get_audio_directory() -> Path:
    """Ensure the persistent audio directory exists and return it."""
    base_dir = settings.data_directory
    base_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = base_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir


@lru_cache
def get_stt_service() -> STTService:
    """Create a singleton STT service instance."""
    return STTService(
        binary_path=settings.whisper_binary,
        model_path=settings.whisper_model,
        language=settings.mock_language,
        use_mock=settings.use_mock_services,
        threads=settings.whisper_threads,
        beam_size=settings.whisper_beam_size,
        best_of=settings.whisper_best_of,
        temperature=settings.whisper_temperature,
        print_timestamps=settings.whisper_print_timestamps,
    )


@lru_cache
def get_tts_service() -> TTSService:
    """Create a singleton TTS service instance."""
    return TTSService(
        binary_path=settings.piper_binary,
        model_path=settings.piper_model,
        use_mock=settings.use_mock_services,
    )


@lru_cache
def get_llm_service() -> LLMService:
    """Create a singleton LLM service client."""
    return LLMService(
        base_url=str(settings.llm_base_url),
        default_model=settings.llm_default_model,
    )


__all__ = [
    "get_audio_directory",
    "get_llm_service",
    "get_stt_service",
    "get_tts_service",
]
