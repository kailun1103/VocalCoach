from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Source text to translate.")
    target_language: str | None = Field(
        default="zh-TW",
        description="BCP-47 language tag for the translation output; defaults to Traditional Chinese.",
    )
    model: str | None = Field(
        default=None,
        description="Optional override model name; falls back to configured translation model.",
    )


class TranslationResponse(BaseModel):
    translated_text: str = Field(..., description="Translated text output.")
    model: str | None = Field(
        default=None,
        description="Model name reported by backend for translation.",
    )
