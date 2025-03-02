from datetime import datetime
from pathlib import Path

import pysrt

from any_translate.models.subtitle import Subtitle


def srt_to_subtitles(srt_contents: list[pysrt.SubRipItem]) -> list[Subtitle]:
    """
    Convert a list of pysrt SubRipItems to a list of Subtitle objects

    Args:
        srt_contents: List of subtitles parsed by pysrt

    Returns:
        List of Subtitle objects
    """
    subtitles = []
    for srt_subtitle in srt_contents:
        subtitle = Subtitle(
            index=srt_subtitle.index,
            start=str(srt_subtitle.start),
            end=str(srt_subtitle.end),
            text=srt_subtitle.text,
        )
        subtitles.append(subtitle)

    return subtitles


def srt_file_to_subtitles(file_path: Path) -> list[Subtitle]:
    """
    Convert an SRT file to a list of Subtitle objects

    Args:
        file_path: Path to the SRT file

    Returns:
        List of Subtitle objects
    """
    srt_subtitles_list = pysrt.open(str(file_path), encoding="utf-8")
    return srt_to_subtitles(srt_subtitles_list)


def subtitles_to_srt(subtitles: list[Subtitle]) -> str:
    """
    Convert a list of Subtitle objects to an SRT format string

    Args:
        subtitles: List of Subtitle objects

    Returns:
        SRT format string
    """
    srt_subtitles: list[pysrt.SubRipItem] = []
    for subtitle in subtitles:
        srt_subtitle = pysrt.SubRipItem(
            index=subtitle.index,
            start=pysrt.SubRipTime.from_string(subtitle.start),
            end=pysrt.SubRipTime.from_string(subtitle.end),
            text=subtitle.text,
        )
        srt_subtitles.append(srt_subtitle)
    return "\n\n".join([str(sub) for sub in srt_subtitles])


def save_subtitles_to_srt(subtitles: list[Subtitle], file_path: Path, reindex: bool = False) -> None:
    """
    Save a list of Subtitle objects to an SRT file

    Args:
        subtitles: List of Subtitle objects
        file_path: Path to save the SRT file
        reindex: Whether to reindex the subtitles (default: False)
    """
    srt_file = pysrt.from_string(subtitles_to_srt(subtitles), encoding="utf-8")
    if reindex:
        srt_file.clean_indexes()
    srt_file.save(str(file_path), encoding="utf-8")


def is_in_valid_time_range(
    original_time_range: tuple[str, str],
    translated_time_range: tuple[str, str],
) -> bool:
    """
    Check if the translated time range is within the original time range

    Args:
        original_time_range: Tuple of (start_time, end_time) for the original subtitle
        translated_time_range: Tuple of (start_time, end_time) for the translated subtitle

    Returns:
        True if the translated time range is within the original time range, False otherwise
    """
    original_start, original_end = original_time_range
    translated_start, translated_end = translated_time_range

    date_format = "%H:%M:%S"

    original_start_date = datetime.strptime(original_start.split(".")[0], date_format)
    original_end_date = datetime.strptime(original_end.split(".")[0], date_format)
    translated_start_date = datetime.strptime(translated_start.split(".")[0], date_format)
    translated_end_date = datetime.strptime(translated_end.split(".")[0], date_format)

    if (
        original_start_date.time() <= translated_start_date.time()
        and translated_end_date.time() <= original_end_date.time()
    ):
        return True

    return False
