"""
FastAPI 依賴注入模組

此模組提供 FastAPI 路由使用的依賴注入函數，
包括服務實例的單例模式建立和資源管理。
"""

from functools import lru_cache
from pathlib import Path

from ..core import settings
from ..services import STTService, TTSService
from ..services.llm import LLMService


@lru_cache
def get_audio_directory() -> Path:
    """
    取得音訊檔案儲存目錄
    
    返回:
        Path: 音訊檔案目錄路徑
    
    說明:
        確保持久化音訊目錄存在並返回其路徑。
        如果目錄不存在，會自動建立。
        使用 lru_cache 確保目錄只檢查和建立一次。
    """
    base_dir = settings.data_directory
    base_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = base_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir


@lru_cache
def get_stt_service() -> STTService:
    """
    取得語音轉文字服務的單例實例
    
    返回:
        STTService: 語音轉文字服務實例
    
    說明:
        建立並返回 STT 服務的單例實例，使用應用程式配置中的參數。
        使用 lru_cache 確保整個應用程式生命週期中只建立一個實例。
    """
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
    """
    取得文字轉語音服務的單例實例
    
    返回:
        TTSService: 文字轉語音服務實例
    
    說明:
        建立並返回 TTS 服務的單例實例，使用應用程式配置中的參數。
        使用 lru_cache 確保整個應用程式生命週期中只建立一個實例。
    """
    return TTSService(
        binary_path=settings.piper_binary,
        model_path=settings.piper_model,
        use_mock=settings.use_mock_services,
    )


@lru_cache
def get_llm_service() -> LLMService:
    """
    取得大型語言模型服務的單例客戶端
    
    返回:
        LLMService: LLM 服務客戶端實例
    
    說明:
        建立並返回 LLM 服務的單例客戶端，用於與本地 OpenAI 相容的
        LLM 伺服器通訊。使用 lru_cache 確保整個應用程式生命週期中
        只建立一個實例。
    """
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
