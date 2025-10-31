import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from .config import settings
from .schemas import (
    TextToSpeechRequest,
    TextToSpeechResponse,
    TranscriptionResponse,
    ChatRequest,
    ChatResponse,
)
from .services import STTService, TTSService
from .services.llm import LLMService
from .ui import render_chat_form, render_stt_form, render_tts_form


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _init_audio_directory(base_dir: Path) -> Path:
    """Ensure the data and audio directories exist, returning the audio path."""
    base_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = base_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir


def _build_stt_service() -> STTService:
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


def _build_tts_service() -> TTSService:
    return TTSService(
        binary_path=settings.piper_binary,
        model_path=settings.piper_model,
        use_mock=settings.use_mock_services,
    )


DATA_DIR = settings.data_directory
AUDIO_DIR = _init_audio_directory(DATA_DIR)
stt_service = _build_stt_service()
tts_service = _build_tts_service()
llm_service = LLMService(
    base_url=str(settings.llm_base_url), default_model=settings.llm_default_model
)

app = FastAPI(
    title="EnglishTalk API",
    version="0.1.0",
    description="Voice processing endpoints plus chat proxy for local LLMs.",
)


def _render_tts_form(
    text_value: str = "",
    audio_data_uri: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    error: Optional[str] = None,
    show_success_notice: bool = False,
    voice_value: Optional[str] = None,
    length_scale_value: Optional[float] = None,
    noise_scale_value: Optional[float] = None,
    noise_w_value: Optional[float] = None,
) -> str:
    """Delegate to the shared TTS form renderer."""
    return render_tts_form(
        text_value=text_value,
        audio_data_uri=audio_data_uri,
        duration_seconds=duration_seconds,
        error=error,
        show_success_notice=show_success_notice,
        voice_value=voice_value,
        length_scale_value=length_scale_value,
        noise_scale_value=noise_scale_value,
        noise_w_value=noise_w_value,
    )


def _parse_optional_float_param(label: str, raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    raw_str = str(raw).strip()
    if not raw_str:
        return None
    try:
        return float(raw_str)
    except ValueError as exc:
        raise ValueError(f"{label} must be numeric") from exc

def _generate_tts_response(
    text: str,
    voice: Optional[str] = None,
    length_scale: Optional[float] = None,
    noise_scale: Optional[float] = None,
    noise_w: Optional[float] = None,
) -> TextToSpeechResponse:
    """Helper to synthesize speech and persist audio for both API and form flows."""
    start_time = time.perf_counter()
    audio_base64, sample_rate = tts_service.synthesize(
        text=text,
        voice=voice,
        length_scale=length_scale,
        noise_scale=noise_scale,
        noise_w=noise_w,
    )

    audio_bytes = base64.b64decode(audio_base64.encode("ascii"))
    audio_path = _persist_audio_bytes(audio_bytes)
    log.debug("Generated TTS audio stored at %s", audio_path)

    elapsed_sec = time.perf_counter() - start_time
    return TextToSpeechResponse(
        audio_base64=audio_base64,
        sample_rate=sample_rate,
        duration_seconds=elapsed_sec,
        voice=voice,
        length_scale=length_scale,
        noise_scale=noise_scale,
        noise_w=noise_w,
    )


def _render_stt_form(
    transcript: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    show_success_notice: bool = False,
) -> str:
    """Delegate to the shared STT form renderer."""
    return render_stt_form(
        transcript=transcript,
        duration_ms=duration_ms,
        error=error,
        show_success_notice=show_success_notice,
    )


def _generate_stt_response(
    audio_bytes: bytes,
    filename: Optional[str] = None,
) -> TranscriptionResponse:
    """Helper to transcribe audio and report duration for API and form usage."""
    start_time = time.perf_counter()
    suffix = Path(filename or "").suffix or ".wav"
    temp_path = _persist_audio_bytes(audio_bytes, suffix=suffix)

    try:
        transcription = stt_service.transcribe(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    log.info("Transcription completed in %.2f ms", elapsed_ms)
    return TranscriptionResponse(text=transcription, duration_ms=elapsed_ms)


def _persist_audio_bytes(audio_bytes: bytes, suffix: str = ".wav") -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    target_path = AUDIO_DIR / f"{timestamp}{suffix}"
    target_path.write_bytes(audio_bytes)
    return target_path


@app.post("/stt", response_model=TranscriptionResponse, tags=["speech"])
async def speech_to_text(file: UploadFile = File(...)) -> TranscriptionResponse:
    """Convert uploaded audio into text using Whisper.cpp."""
    audio_bytes = await file.read()
    return _generate_stt_response(audio_bytes, filename=file.filename)


@app.post("/tts", response_model=TextToSpeechResponse, tags=["speech"])
async def text_to_speech(request: TextToSpeechRequest) -> TextToSpeechResponse:
    """Convert text into speech audio using Piper."""
    return _generate_tts_response(
        text=request.text,
        voice=request.voice,
        length_scale=request.length_scale,
        noise_scale=request.noise_scale,
        noise_w=request.noise_w,
    )


@app.get("/tts/form", response_class=HTMLResponse, include_in_schema=False)
async def text_to_speech_form() -> HTMLResponse:
    """Serve a simple web form for manual TTS testing."""
    return HTMLResponse(content=_render_tts_form())


@app.post("/tts/form", response_class=HTMLResponse, include_in_schema=False)
async def text_to_speech_form_submit(
    text: str = Form(...),
    voice: Optional[str] = Form(None),
    length_scale: Optional[str] = Form(None),
    noise_scale: Optional[str] = Form(None),
    noise_w: Optional[str] = Form(None),
) -> HTMLResponse:
    """Handle form submissions and render the TTS result inline."""
    voice_value = (voice or "").strip() or None
    length_value: Optional[float] = None
    noise_value: Optional[float] = None
    noise_w_value: Optional[float] = None
    try:
        length_value = _parse_optional_float_param("Length Scale", length_scale)
        noise_value = _parse_optional_float_param("Noise Scale", noise_scale)
        noise_w_value = _parse_optional_float_param("Noise W", noise_w)
        result = _generate_tts_response(
            text=text,
            voice=voice_value,
            length_scale=length_value,
            noise_scale=noise_value,
            noise_w=noise_w_value,
        )
        audio_data_uri = f"data:audio/wav;base64,{result.audio_base64}"
        content = _render_tts_form(
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
        content = _render_tts_form(
            text_value=text,
            error=str(exc),
            voice_value=voice_value,
            length_scale_value=length_value,
            noise_scale_value=noise_value,
            noise_w_value=noise_w_value,
        )
        return HTMLResponse(content=content, status_code=500)

    return HTMLResponse(content=content)


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """Proxy chat to local OpenAI-compatible LLM server (e.g., LM Studio/Ollama)."""
    content, raw = await llm_service.chat(
        messages=[m.model_dump() for m in request.messages],
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    usage = raw.get("usage") or {}
    choice0 = (raw.get("choices") or [{}])[0]
    return ChatResponse(
        content=content,
        model=raw.get("model"),
        finish_reason=choice0.get("finish_reason"),
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )


@app.post("/chat/stream", response_class=StreamingResponse, tags=["chat"])
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream chat completions via Server-Sent Events."""

    async def event_generator():
        try:
            async for event in llm_service.chat_stream(
                messages=[m.model_dump() for m in request.messages],
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                yield event
        except asyncio.CancelledError:
            log.debug("Client closed chat stream early")
            raise

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@app.get("/chat/form", response_class=HTMLResponse, include_in_schema=False)
async def chat_form() -> HTMLResponse:
    """Serve a lightweight chat playground that uses the streaming endpoint."""
    return HTMLResponse(content=render_chat_form())

@app.get("/stt/form", response_class=HTMLResponse, include_in_schema=False)
async def speech_to_text_form() -> HTMLResponse:
    """Serve a simple web form for manual STT testing."""
    return HTMLResponse(content=_render_stt_form())


@app.post("/stt/form", response_class=HTMLResponse, include_in_schema=False)
async def speech_to_text_form_submit(file: UploadFile = File(...)) -> HTMLResponse:
    """Handle audio uploads and render the STT result inline."""
    try:
        audio_bytes = await file.read()
        result = _generate_stt_response(audio_bytes, filename=file.filename)
        content = _render_stt_form(
            transcript=result.text,
            duration_ms=result.duration_ms,
            show_success_notice=True,
        )
    except Exception as exc:  # pragma: no cover - surface error message to UI
        log.exception("STT form submission failed")
        content = _render_stt_form(error=str(exc))
        return HTMLResponse(content=content, status_code=500)

    return HTMLResponse(content=content)


_FAVICON_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAksB9gptOq8AAAAASUVORK5CYII="
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Serve a minimal favicon to avoid 404s in the form UI."""
    return Response(content=_FAVICON_BYTES, media_type="image/png")
