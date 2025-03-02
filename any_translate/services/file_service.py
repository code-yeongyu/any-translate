import asyncio
import math
import textwrap
from pathlib import Path

from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from any_translate.cli.console import console
from any_translate.models.subtitle import Subtitle
from any_translate.services.translation_service import TranslationService
from any_translate.utils.srt import save_subtitles_to_srt, srt_file_to_subtitles


async def process_srt_file(
    input_path: Path,
    output_path: Path,
    translation_service: TranslationService,
    sessions: int = 1,
) -> None:
    """
    Process SRT file

    Args:
        input_path: Input file path
        output_path: Output file path
        translation_service: Translation service instance
        sessions: Number of concurrent sessions
    """
    # Load SRT file
    subtitles = srt_file_to_subtitles(input_path)
    total_subtitles = len(subtitles)
    console.print(f"Total number of subtitles: {total_subtitles}")

    # Calculate subtitles per group (distribute evenly)
    group_size: int = math.ceil(total_subtitles / sessions)
    groups: list[list[Subtitle]] = [subtitles[i * group_size : (i + 1) * group_size] for i in range(sessions)]
    # Calculate starting index for each group to maintain global order (starting from 1)
    group_starts: list[int] = [i * group_size + 1 for i in range(sessions)]

    # Create independent TranslationService instances for each session (different contexts)
    translation_services: list[TranslationService] = [
        TranslationService(
            openai_client=translation_service.client,
            model_names=translation_service.model_names,
            system_prompt=translation_service.system_prompt,
            additional_prompt=translation_service.additional_prompt,
            target_lang=translation_service.target_lang,
            max_tokens=translation_service.max_tokens,
        )
        for _ in range(sessions)
    ]

    # Use a single Progress for progress display
    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Translating", total=total_subtitles)

        # Return results from each session as a list of tuples: (global_index, translated_subtitle)
        async def process_session(
            session_start: int, subtitles_subset: list[Subtitle], ts: TranslationService
        ) -> list[tuple[int, Subtitle]]:
            """
            Process a subset of subtitles in a session

            Args:
                session_start: Starting index for this session
                subtitles_subset: Subset of subtitles to process
                ts: Translation service instance for this session

            Returns:
                List of tuples containing (original_index, translated_subtitle)
            """
            session_results: list[tuple[int, Subtitle]] = []
            for local_idx, subtitle in enumerate(subtitles_subset):
                global_idx = session_start + local_idx
                try:
                    result = await ts.translate_sentence(subtitle.text)
                    console.print(
                        textwrap.dedent(f"""
                    ========================================
                    Session {global_idx}

                    Original:
                    {subtitle.text}

                    Translated:
                    {result["translated_text"]}
                    """).strip()
                    )
                    # Create translated subtitle
                    translated_subtitle = Subtitle(
                        index=subtitle.index,
                        start=subtitle.start,
                        end=subtitle.end,
                        text=result["translated_text"],
                    )
                    # Store global index and translation result together
                    session_results.append((global_idx, translated_subtitle))
                except Exception as e:
                    console.print("Error processing subtitle:")
                    console.print(subtitle.text)
                    console.print(e)
                    # Keep original subtitle in case of error
                    session_results.append((global_idx, subtitle))
                console.print()  # Empty line for separation
                progress.advance(task, 1)
            return session_results

        # Create async tasks for each session
        tasks = [process_session(group_starts[i], groups[i], translation_services[i]) for i in range(sessions)]
        session_results_lists: list[list[tuple[int, Subtitle]]] = await asyncio.gather(*tasks)

    # Combine results from all sessions
    all_results: list[tuple[int, Subtitle]] = []
    for res in session_results_lists:
        all_results.extend(res)
    # Sort by global index to maintain original subtitle order
    all_results.sort(key=lambda x: x[0])

    # Create list of translated subtitles
    translated_subtitles = [subtitle for _, subtitle in all_results]

    # Save translated subtitles to SRT file
    save_subtitles_to_srt(translated_subtitles, output_path)
    console.print(f"Translation completed: {output_path}")


async def process_text_file(
    input_path: Path,
    output_path: Path,
    translation_service: TranslationService,
    sessions: int = 1,
) -> None:
    """
    Process text file

    Args:
        input_path: Input file path
        output_path: Output file path
        translation_service: Translation service instance
        sessions: Number of concurrent sessions
    """
    with input_path.open("r", encoding="utf-8") as f:
        text = f.read()

    # Simple sentence splitting (by newline)
    sentences = [s.strip() + "\n" for s in text.split("\n") if s.strip()]
    total_sentences = len(sentences)
    console.print(f"Total number of sentences: {total_sentences}")

    # Calculate sentences per group (distribute evenly)
    group_size: int = math.ceil(total_sentences / sessions)
    groups: list[list[str]] = [sentences[i * group_size : (i + 1) * group_size] for i in range(sessions)]
    # Calculate starting index for each group to maintain global order (starting from 1)
    group_starts: list[int] = [i * group_size + 1 for i in range(sessions)]

    # Create independent TranslationService instances for each session (different contexts)
    translation_services: list[TranslationService] = [
        TranslationService(
            openai_client=translation_service.client,
            model_names=translation_service.model_names,
            system_prompt=translation_service.system_prompt,
            additional_prompt=translation_service.additional_prompt,
            target_lang=translation_service.target_lang,
            max_tokens=translation_service.max_tokens,
        )
        for _ in range(sessions)
    ]

    # Use a single Progress for progress display
    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Translating", total=total_sentences)

        # Return results from each session as a list of tuples: (global_index, translated_sentence)
        async def process_session(
            session_start: int, sentences_subset: list[str], ts: TranslationService
        ) -> list[tuple[int, str]]:
            """
            Process a subset of sentences in a session

            Args:
                session_start: Starting index for this session
                sentences_subset: Subset of sentences to process
                ts: Translation service instance for this session

            Returns:
                List of tuples containing (original_index, translated_sentence)
            """
            session_results: list[tuple[int, str]] = []
            for local_idx, sentence in enumerate(sentences_subset):
                global_idx = session_start + local_idx
                console.print("=" * 40)
                console.print(f"Session {global_idx}")
                console.print("Translating:")
                console.print(sentence)
                try:
                    result = await ts.translate_sentence(sentence)
                    # Store global index and translation result together
                    session_results.append((global_idx, result["translated_text"]))
                except Exception as e:
                    console.print("Error processing sentence:")
                    console.print(sentence)
                    console.print(e)
                    session_results.append((global_idx, f"Error: {e}"))
                console.print()  # Empty line for separation
                progress.advance(task, 1)
            return session_results

        # Create async tasks for each session
        tasks = [process_session(group_starts[i], groups[i], translation_services[i]) for i in range(sessions)]
        session_results_lists: list[list[tuple[int, str]]] = await asyncio.gather(*tasks)

    # Combine results from all sessions
    all_results: list[tuple[int, str]] = []
    for res in session_results_lists:
        all_results.extend(res)
    # Sort by global index to maintain original sentence order
    all_results.sort(key=lambda x: x[0])

    # Write results to output file after all processing is complete
    with output_path.open("w", encoding="utf-8") as out_file:
        for _, translated_text in all_results:
            out_file.write(translated_text + "\n")
            out_file.flush()

    console.print(f"Translation completed: {output_path}")
