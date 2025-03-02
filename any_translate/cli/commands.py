import asyncio
import os
from pathlib import Path

import typer
from openai import AsyncOpenAI

from any_translate.cli.console import console
from any_translate.models.translation import TranslationOptions
from any_translate.services.file_service import process_srt_file, process_text_file
from any_translate.services.translation_service import TranslationService
from any_translate.utils.prompt import get_system_prompt

app = typer.Typer(help="A tool for translating subtitle and text files using OpenAI API")


@app.command("translate")
def translate(
    input_file: Path = typer.Argument(..., help="Input SRT file path", exists=True, dir_okay=False, resolve_path=True),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Output file path (default: input_filename_target_lang.extension)"
    ),
    source_lang: str = typer.Option("auto", "--source-lang", "-s", help="Source language (default: auto)"),
    target_lang: str = typer.Option("ko", "--target-lang", "-t", help="Target language (default: ko)"),
    openai_api_key: str | None = typer.Option(
        None, "--openai-api-key", help="OpenAI API key (can also be set via OPENAI_API_KEY environment variable)"
    ),
    base_url: str | None = typer.Option(
        None, "--base-url", help="OpenAI API base URL (can be used to override the default base URL)"
    ),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="OpenAI model to use (default: gpt-4o-mini)"),
    sessions: int = typer.Option(
        1, "--sessions", "-n", help="Number of sessions to process simultaneously (default: 1)"
    ),
    temperature: float = typer.Option(1.0, "--temperature", "-T", help="Model temperature value (default: 1.0)"),
    tone: str = typer.Option(
        "auto-contextual",
        "--tone",
        help="Translation tone (formal, informal, auto-contextual) (default: auto-contextual)",
    ),
    system_prompt_file: Path | None = typer.Option(
        None, "--system-prompt-file", "-p", help="System prompt file for translation"
    ),
    additional_prompt: str | None = typer.Option(
        None, "--additional-prompt", help="Additional prompt to add after the system prompt"
    ),
) -> None:
    """
    Translate SRT subtitle files.
    """
    # Set default output file path if not specified
    if output_file is None:
        output_file = input_file.with_name(f"{input_file.stem}_{target_lang}{input_file.suffix}")

    # Set API key
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        typer.echo(
            "OpenAI API key is required. Please set it using the --openai-api-key option or OPENAI_API_KEY environment variable."
        )
        raise typer.Exit(code=1)

    # Set translation options
    options = TranslationOptions(
        source_lang=source_lang,
        target_lang=target_lang,
        model=model,
        temperature=temperature,
        tone=tone,  # type: ignore
        sessions=sessions,
    )

    # Generate system prompt
    system_prompt = get_system_prompt(
        target_lang=options.target_lang,
        tone=options.tone,
        system_prompt_file=system_prompt_file,
        additional_prompt=additional_prompt,
    )

    # Create OpenAI client
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # Create translation service
    translation_service = TranslationService(
        openai_client=client,
        model_names=[options.model],
        system_prompt=system_prompt,
        target_lang=options.target_lang,
        additional_prompt=additional_prompt,
    )

    # Process subtitle file
    console.print(f"[bold]Input file:[/bold] {input_file}")
    console.print(f"[bold]Output file:[/bold] {output_file}")
    console.print(f"[bold]Source language:[/bold] {options.source_lang}")
    console.print(f"[bold]Target language:[/bold] {options.target_lang}")
    console.print(f"[bold]Model:[/bold] {options.model}")
    console.print(f"[bold]Number of sessions:[/bold] {options.sessions}")
    console.print(f"[bold]Translation tone:[/bold] {options.tone}")
    if base_url:
        console.print(f"[bold]Base URL:[/bold] {base_url}")

    try:
        asyncio.run(process_srt_file(input_file, output_file, translation_service, options.sessions))
    except Exception as e:
        console.print(f"[bold red]Error occurred:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("translate-text")
def translate_text(
    input_file: Path = typer.Argument(
        ..., help="Input text file path", exists=True, dir_okay=False, resolve_path=True
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Output file path (default: input_filename_target_lang.extension)"
    ),
    source_lang: str = typer.Option("auto", "--source-lang", "-s", help="Source language (default: auto)"),
    target_lang: str = typer.Option("ko", "--target-lang", "-t", help="Target language (default: ko)"),
    openai_api_key: str | None = typer.Option(
        None, "--openai-api-key", help="OpenAI API key (can also be set via OPENAI_API_KEY environment variable)"
    ),
    base_url: str | None = typer.Option(
        None, "--base-url", help="OpenAI API base URL (can be used to override the default base URL)"
    ),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="OpenAI model to use (default: gpt-4o-mini)"),
    sessions: int = typer.Option(
        1, "--sessions", "-n", help="Number of sessions to process simultaneously (default: 1)"
    ),
    temperature: float = typer.Option(1.0, "--temperature", "-T", help="Model temperature value (default: 1.0)"),
    tone: str = typer.Option(
        "auto-contextual",
        "--tone",
        help="Translation tone (formal, informal, auto-contextual) (default: auto-contextual)",
    ),
    system_prompt_file: Path | None = typer.Option(
        None, "--system-prompt-file", "-p", help="System prompt file for translation"
    ),
    additional_prompt: str | None = typer.Option(
        None, "--additional-prompt", help="Additional prompt to add after the system prompt"
    ),
) -> None:
    """
    Translate text files.
    """
    # Set default output file path if not specified
    if output_file is None:
        output_file = input_file.with_name(f"{input_file.stem}_{target_lang}{input_file.suffix}")

    # Set API key
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        typer.echo(
            "OpenAI API key is required. Please set it using the --openai-api-key option or OPENAI_API_KEY environment variable."
        )
        raise typer.Exit(code=1)

    # Set translation options
    options = TranslationOptions(
        source_lang=source_lang,
        target_lang=target_lang,
        model=model,
        temperature=temperature,
        tone=tone,  # type: ignore
        sessions=sessions,
    )

    # Generate system prompt
    system_prompt = get_system_prompt(
        target_lang=options.target_lang,
        tone=options.tone,
        system_prompt_file=system_prompt_file,
        additional_prompt=additional_prompt,
    )

    # Create OpenAI client
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # Create translation service
    translation_service = TranslationService(
        openai_client=client,
        model_names=[options.model],
        system_prompt=system_prompt,
        target_lang=options.target_lang,
        additional_prompt=additional_prompt,
    )

    # Process text file
    console.print(f"[bold]Input file:[/bold] {input_file}")
    console.print(f"[bold]Output file:[/bold] {output_file}")
    console.print(f"[bold]Source language:[/bold] {options.source_lang}")
    console.print(f"[bold]Target language:[/bold] {options.target_lang}")
    console.print(f"[bold]Model:[/bold] {options.model}")
    console.print(f"[bold]Number of sessions:[/bold] {options.sessions}")
    console.print(f"[bold]Translation tone:[/bold] {options.tone}")
    if base_url:
        console.print(f"[bold]Base URL:[/bold] {base_url}")

    try:
        asyncio.run(process_text_file(input_file, output_file, translation_service, options.sessions))
    except Exception as e:
        console.print(f"[bold red]Error occurred:[/bold red] {e}")
        raise typer.Exit(code=1)
