"""
語音處理工作流程模組

此模組提供語音轉文字和文字轉語音的完整工作流程，
包括音訊處理、服務調用和結果封裝。
"""

from pathlib import Path
from typing import Optional
import time

from ...schemas.speech import (
    TextToSpeechRequest,
    TextToSpeechResponse,
    TranscriptionResponse,
)
from ...services import STTService, TTSService
from ...utils import decode_audio_base64, save_audio_bytes


def generate_tts_response(
    tts_service: TTSService,
    audio_dir: Path,
    request: TextToSpeechRequest,
) -> TextToSpeechResponse:
    """
    生成文字轉語音回應
    
    參數:
        tts_service: 文字轉語音服務實例
        audio_dir: 音訊儲存目錄
        request: 文字轉語音請求物件
    
    返回:
        TextToSpeechResponse: 包含音訊資料和相關資訊的回應物件
    
    說明:
        合成語音並將生成的音訊持久化以便稽核。
    """
    start_time = time.perf_counter()
    
    # 使用 TTS 服務合成語音
    audio_base64, sample_rate = tts_service.synthesize(
        text=request.text,
        voice=request.voice,
        length_scale=request.length_scale,
        noise_scale=request.noise_scale,
        noise_w=request.noise_w,
    )

    # 解碼並儲存音訊檔案
    audio_bytes = decode_audio_base64(audio_base64)
    save_audio_bytes(audio_dir, audio_bytes)

    # 計算處理時間
    elapsed_seconds = time.perf_counter() - start_time
    
    return TextToSpeechResponse(
        audio_base64=audio_base64,
        sample_rate=sample_rate,
        duration_seconds=elapsed_seconds,
        voice=request.voice,
        length_scale=request.length_scale,
        noise_scale=request.noise_scale,
        noise_w=request.noise_w,
    )


def generate_stt_response(
    stt_service: STTService,
    audio_dir: Path,
    audio_bytes: bytes,
    filename: Optional[str] = None,
) -> TranscriptionResponse:
    """
    生成語音轉文字回應
    
    參數:
        stt_service: 語音轉文字服務實例
        audio_dir: 音訊儲存目錄
        audio_bytes: 原始音訊位元組資料
        filename: 原始檔案名稱（可選，用於判斷副檔名）
    
    返回:
        TranscriptionResponse: 包含轉寫文字和處理時間的回應物件
    
    說明:
        轉寫音訊內容並回報總處理時長。
        臨時音訊檔案在處理後會被自動刪除。
    """
    start_time = time.perf_counter()
    
    # 確定檔案副檔名
    suffix = Path(filename or "").suffix or ".wav"
    
    # 儲存臨時音訊檔案
    temp_path = save_audio_bytes(audio_dir, audio_bytes, suffix=suffix)

    try:
        # 執行語音轉文字
        transcription = stt_service.transcribe(temp_path)
    finally:
        # 清理臨時檔案
        temp_path.unlink(missing_ok=True)

    # 計算處理時間（毫秒）
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    
    return TranscriptionResponse(text=transcription, duration_ms=elapsed_ms)
