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
    """Synthesize speech and persist the resulting audio for auditing."""
    start_time = time.perf_counter()
    audio_base64, sample_rate = tts_service.synthesize(
        text=request.text,
        voice=request.voice,
        length_scale=request.length_scale,
        noise_scale=request.noise_scale,
        noise_w=request.noise_w,
    )

    audio_bytes = decode_audio_base64(audio_base64)
    save_audio_bytes(audio_dir, audio_bytes)

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
    """Transcribe audio content and report the total processing duration."""
    start_time = time.perf_counter()
    suffix = Path(filename or "").suffix or ".wav"
    temp_path = save_audio_bytes(audio_dir, audio_bytes, suffix=suffix)

    try:
        transcription = stt_service.transcribe(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return TranscriptionResponse(text=transcription, duration_ms=elapsed_ms)
