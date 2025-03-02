from dataclasses import dataclass
from typing import Literal, TypedDict, cast

from pydantic import BaseModel, Field


class TranslationResult(TypedDict):
    """TypedDict containing translation results"""

    source_lang: str
    translated_text: str


class TranslationSchema(BaseModel):
    """Pydantic model containing translation results"""

    source_lang: str = Field(description="Source language of the text")
    translated_text: str = Field(description="Translated text in target language")

    class Config:
        json_schema_extra = {"examples": [{"source_lang": "EN", "translated_text": "Translated text"}]}

    def to_result(self) -> TranslationResult:
        """Convert Pydantic model to TypedDict format"""
        return cast(TranslationResult, self.model_dump(mode="python"))


@dataclass
class TranslationOptions:
    """
    Data class for storing translation options
    """

    source_lang: str = "auto"
    target_lang: str = "ko"
    model: str = "gpt-4o-mini"
    temperature: float = 1.0
    tone: Literal["formal", "informal", "auto-contextual"] = "auto-contextual"
    sessions: int = 1
