from typing import TypedDict

from pydantic import BaseModel, Field, TypeAdapter


class SubtitleTypedDict(TypedDict):
    index: int
    start: str
    end: str
    text: str


class Subtitle(BaseModel):
    """Basic data model containing subtitle information"""

    index: int = Field(examples=[1])
    start: str = Field(examples=["00:00:00,000"])
    end: str = Field(examples=["00:00:00,000"])
    text: str = Field(examples=["Hello world"])


SubtitleList = TypeAdapter(list[Subtitle])


def subtitles_to_dict(subtitles: list[Subtitle]) -> list[SubtitleTypedDict]:
    """Convert a list of subtitle objects to a list of dictionaries"""
    return SubtitleList.dump_python(subtitles)


def subtitles_to_json(subtitles: list[Subtitle]) -> str:
    """Convert a list of subtitle objects to a JSON string"""
    return str(SubtitleList.dump_json(subtitles))
