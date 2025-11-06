"""
服務層入口點模組

此模組提供語音處理服務的統一匯出點，
包括語音轉文字（STT）和文字轉語音（TTS）服務。
"""

from .stt import STTService
from .tts import TTSService

__all__ = ["STTService", "TTSService"]
