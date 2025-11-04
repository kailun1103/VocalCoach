from typing import List

from pydantic import BaseModel, Field


class DictionaryRequest(BaseModel):
    word: str = Field(..., description="Target word selected by the learner.")
    sentence: str = Field(
        default="",
        description="Full sentence context where the word appears.",
    )
    model: str | None = Field(
        default=None,
        description="Optional override model name for dictionary lookups.",
    )


class DictionaryResponse(BaseModel):
    headword: str = Field(..., description="Normalized dictionary entry headword.")
    part_of_speech: str | None = Field(
        default=None,
        description="Part of speech label (e.g. noun, verb) when available.",
    )
    phonetics: List[str] = Field(
        default_factory=list,
        description="Pronunciation strings such as IPA or phonetic hints.",
    )
    definition: str = Field(
        ...,
        description="Definition that mixes English meaning with Traditional Chinese support.",
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example sentences demonstrating usage.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional Traditional Chinese notes or learning tips.",
    )
    model: str | None = Field(
        default=None,
        description="Model actually used by the LLM backend.",
    )
