from typing import List, Literal, Optional

from pydantic import BaseModel, Field


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
