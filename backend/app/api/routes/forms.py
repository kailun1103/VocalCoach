import base64
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response

from ...schemas.speech import TextToSpeechRequest
from ...services import STTService, TTSService
from ...ui import render_chat_form, render_stt_form, render_tts_form
from ..dependencies import (
    get_audio_directory,
    get_stt_service,
    get_tts_service,
)
from ..workflows import generate_stt_response, generate_tts_response

log = logging.getLogger(__name__)
router = APIRouter(include_in_schema=False)

_FAVICON_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAksB9gptOq8AAAAASUVORK5CYII="
)


def _parse_optional_float(label: str, raw: Optional[str]) -> Optional[float]:
    """Convert a possibly-empty form value into a float or None."""
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc


@router.get("/chat/form", response_class=HTMLResponse)
async def chat_form() -> HTMLResponse:
    """Serve a lightweight chat playground that uses the streaming endpoint."""
    return HTMLResponse(content=render_chat_form())


@router.get("/tts/form", response_class=HTMLResponse)
async def text_to_speech_form() -> HTMLResponse:
    """Serve a simple web form for manual TTS testing."""
    return HTMLResponse(content=render_tts_form())


@router.post("/tts/form", response_class=HTMLResponse)
async def text_to_speech_form_submit(
    text: str = Form(...),
    voice: Optional[str] = Form(None),
    length_scale: Optional[str] = Form(None),
    noise_scale: Optional[str] = Form(None),
    noise_w: Optional[str] = Form(None),
    tts_service: TTSService = Depends(get_tts_service),
    audio_dir: Path = Depends(get_audio_directory),
) -> HTMLResponse:
    """Handle form submissions and render the TTS result inline."""
    voice_value = (voice or "").strip() or None
    length_value: Optional[float] = None
    noise_value: Optional[float] = None
    noise_w_value: Optional[float] = None

    try:
        length_value = _parse_optional_float("Length Scale", length_scale)
        noise_value = _parse_optional_float("Noise Scale", noise_scale)
        noise_w_value = _parse_optional_float("Noise W", noise_w)
        request = TextToSpeechRequest(
            text=text,
            voice=voice_value,
            length_scale=length_value,
            noise_scale=noise_value,
            noise_w=noise_w_value,
        )
        result = generate_tts_response(
            tts_service=tts_service,
            audio_dir=audio_dir,
            request=request,
        )
        audio_data_uri = f"data:audio/wav;base64,{result.audio_base64}"
        content = render_tts_form(
            text_value=text,
            audio_data_uri=audio_data_uri,
            duration_seconds=result.duration_seconds,
            voice_value=result.voice,
            length_scale_value=result.length_scale,
            noise_scale_value=result.noise_scale,
            noise_w_value=result.noise_w,
            show_success_notice=True,
        )
    except Exception as exc:  # pragma: no cover - surface error message to UI
        log.exception("TTS form submission failed")
        content = render_tts_form(
            text_value=text,
            error=str(exc),
            voice_value=voice_value,
            length_scale_value=length_value,
            noise_scale_value=noise_value,
            noise_w_value=noise_w_value,
        )
        return HTMLResponse(content=content, status_code=500)

    return HTMLResponse(content=content)


@router.get("/stt/form", response_class=HTMLResponse)
async def speech_to_text_form() -> HTMLResponse:
    """Serve a simple web form for manual STT testing."""
    return HTMLResponse(content=render_stt_form())


@router.post("/stt/form", response_class=HTMLResponse)
async def speech_to_text_form_submit(
    file: UploadFile = File(...),
    stt_service: STTService = Depends(get_stt_service),
    audio_dir: Path = Depends(get_audio_directory),
) -> HTMLResponse:
    """Handle audio uploads and render the STT result inline."""
    try:
        audio_bytes = await file.read()
        result = generate_stt_response(
            stt_service=stt_service,
            audio_dir=audio_dir,
            audio_bytes=audio_bytes,
            filename=file.filename,
        )
        content = render_stt_form(
            transcript=result.text,
            duration_ms=result.duration_ms,
            show_success_notice=True,
        )
    except Exception as exc:  # pragma: no cover - surface error message to UI
        log.exception("STT form submission failed")
        content = render_stt_form(error=str(exc))
        return HTMLResponse(content=content, status_code=500)

    return HTMLResponse(content=content)


@router.get("/favicon.ico")
async def favicon() -> Response:
    """Serve a minimal favicon to avoid 404s in the form UI."""
    return Response(content=_FAVICON_BYTES, media_type="image/png")
