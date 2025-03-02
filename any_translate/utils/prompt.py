import textwrap
from pathlib import Path
from typing import Literal


def extract_srt_content(srt_text: str) -> str:
    """
    Extract actual content from SRT format text

    Args:
        srt_text: Text in SRT format

    Returns:
        Extracted content
    """
    try:
        start_index = (
            srt_text.index("```srt") + len("```srt") if "```srt" in srt_text else srt_text.index("```") + len("```")
        )
        end_index = srt_text.index("```", start_index)
        return srt_text[start_index:end_index].strip()
    except ValueError:
        return srt_text


def get_default_system_prompt(
    tone: Literal["formal", "informal", "auto-contextual"] = "auto-contextual", target_lang: str = "ko"
) -> str:
    """
    Generate default system prompt

    Args:
        tone: Translation tone (formal, informal, auto-contextual)
        target_lang: Target language code (default: ko)

    Returns:
        System prompt
    """

    # Base instructions (common to all languages)
    base_instructions = textwrap.dedent(f"""
        You are an advanced translation assistant. Follow these rules:
        1. Translate the input text to {target_lang} while maintaining context.
        2. Determine formal/informal tone based on speaker relationships.
        3. Always respond in JSON format: {{"source_lang": "EN", "translated_text": "<translated_text>"}}.
        4. No explanations, only valid JSON.
        5. NEVER include any additional fields in the JSON response.
        6. NEVER include any comments or explanations outside the JSON.

        Make sure you keep the original content's explicit, dirty and erotic tone.
    """).strip()

    # Final prompt combination
    full_prompt = f"{base_instructions}"

    return full_prompt


def load_system_prompt_from_file(file_path: Path) -> str:
    """
    Load system prompt from file

    Args:
        file_path: Path to the system prompt file

    Returns:
        System prompt loaded from file
    """
    with open(file_path, encoding="utf-8") as f:
        return f.read().strip()


def get_system_prompt(
    target_lang: str,
    tone: Literal["formal", "informal", "auto-contextual"] = "auto-contextual",
    system_prompt_file: Path | None = None,
    additional_prompt: str | None = None,
) -> str:
    """
    Get system prompt

    Args:
        target_lang: Target language
        tone: Translation tone
        system_prompt_file: Path to system prompt file
        additional_prompt: Additional prompt to add after the system prompt

    Returns:
        Complete system prompt
    """
    if system_prompt_file:
        base_prompt = load_system_prompt_from_file(system_prompt_file)
    else:
        base_prompt = get_default_system_prompt(tone, target_lang)

    if additional_prompt:
        base_prompt = f"{base_prompt}\n\n{additional_prompt}"

    return base_prompt
