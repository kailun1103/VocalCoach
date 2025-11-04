from pydantic import BaseModel, Field


class GrammarCheckRequest(BaseModel):
    text: str = Field(..., description="Text to evaluate for grammatical correctness.")
    model: str | None = Field(
        default=None,
        description="Optional override model name used for grammar checking.",
    )


class GrammarCheckResponse(BaseModel):
    is_correct: bool = Field(..., description="Indicates whether the original text is grammatically sound.")
    feedback: str = Field(..., description="Explanation about any issues or confirmation of correctness.")
    suggestion: str | None = Field(
        default=None,
        description="Suggested revision of the text when applicable.",
    )
    model: str | None = Field(
        default=None,
        description="Model name reported by the backend for grammar checking.",
    )
