from typing import Literal, List, Optional

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str = Field(..., description="Transcribed text output.")
    duration_ms: float = Field(
        ..., description="Total time spent handling the transcription request in milliseconds."
    )


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., description="Text to convert into speech audio.")
    voice: str | None = Field(
        default=None,
        description="Optional voice identifier for multi-speaker models.",
    )
    length_scale: float | None = Field(
        default=None,
        ge=0.1,
        description="Prosody control: >1 slows down speech, <1 speeds it up.",
    )
    noise_scale: float | None = Field(
        default=None,
        ge=0.0,
        description="Controls variation in speech energy; lower is calmer.",
    )
    noise_w: float | None = Field(
        default=None,
        ge=0.0,
        description="Controls phoneme width variation; higher is more expressive.",
    )


class TextToSpeechResponse(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio payload.")
    sample_rate: int = Field(..., description="Audio sample rate in Hz.")
    duration_seconds: float = Field(
        ..., description="Total time spent generating the speech audio in seconds."
    )
    voice: str | None = Field(
        default=None,
        description="Voice identifier used during synthesis.",
    )
    length_scale: float | None = Field(
        default=None,
        description="Prosody length_scale value applied during synthesis.",
    )
    noise_scale: float | None = Field(
        default=None,
        description="Prosody noise_scale value applied during synthesis.",
    )
    noise_w: float | None = Field(
        default=None,
        description="Prosody noise_w value applied during synthesis.",
    )


# -------------------------
# Chat/LLM schemas
# -------------------------

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(
        ..., description="Chat role per OpenAI-like API."
    )
    content: str = Field(..., description="Message content text.")


class ChatRequest(BaseModel):
    model: Optional[str] = Field(
        default=None,
        description="Model name; uses server default when omitted.",
    )
    messages: List[ChatMessage] = Field(
        default_factory=list, description="Conversation messages in order."
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature forwarded to the LLM."
    )
    max_tokens: int | None = Field(
        default=None, description="Max tokens for completion; optional."
    )


class ChatResponse(BaseModel):
    content: str = Field(..., description="Assistant reply content.")
    model: str | None = Field(
        default=None, description="Model name reported by backend."
    )
    finish_reason: str | None = Field(
        default=None, description="Reason the generation stopped."
    )
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
