"""HTML form renderers for the FastAPI demo interfaces."""

from .chat_form import render_chat_form
from .stt_form import render_stt_form
from .tts_form import render_tts_form

__all__ = ["render_chat_form", "render_stt_form", "render_tts_form"]
