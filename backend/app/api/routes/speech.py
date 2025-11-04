from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from ...schemas.speech import (
    TextToSpeechRequest,
    TextToSpeechResponse,
    TranscriptionResponse,
)
from ...services import STTService, TTSService
from ..dependencies import (
    get_audio_directory,
    get_stt_service,
    get_tts_service,
)
from ..workflows import generate_stt_response, generate_tts_response

router = APIRouter(tags=["speech"])


@router.post("/stt", response_model=TranscriptionResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    stt_service: STTService = Depends(get_stt_service),
    audio_dir: Path = Depends(get_audio_directory),
) -> TranscriptionResponse:
    """Convert uploaded audio into text using Whisper.cpp."""
    audio_bytes = await file.read()
    return generate_stt_response(
        stt_service=stt_service,
        audio_dir=audio_dir,
        audio_bytes=audio_bytes,
        filename=file.filename,
    )


@router.post("/tts", response_model=TextToSpeechResponse)
async def text_to_speech(
    request: TextToSpeechRequest,
    tts_service: TTSService = Depends(get_tts_service),
    audio_dir: Path = Depends(get_audio_directory),
) -> TextToSpeechResponse:
    """Convert text into speech audio using Piper."""
    return generate_tts_response(
        tts_service=tts_service,
        audio_dir=audio_dir,
        request=request,
    )
