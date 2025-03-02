import json
import textwrap
from typing import Any, cast

import tiktoken
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError
from rich import print
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from any_translate.models.translation import TranslationResult, TranslationSchema


class TranslationService:
    """
    Translation Service Class

    Provides a service for translating text using the OpenAI API.
    """

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        model_names: list[str],
        system_prompt: str,
        target_lang: str,
        additional_prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> None:
        """
        Initialize TranslationService

        Args:
            openai_client: Injected OpenAI async client instance
            model_names: List of available model names (tried in order of priority)
            system_prompt: System prompt string (for providing translation guidelines)
            max_tokens: Maximum number of tokens (default: 4096)
        """
        self.client = openai_client
        self.model_names = model_names
        self.system_prompt = system_prompt
        self.target_lang = target_lang
        self.additional_prompt = additional_prompt
        self.max_tokens = max_tokens
        self.history: list[ChatCompletionMessageParam] = []
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, messages: list[ChatCompletionMessageParam]) -> int:
        """
        Count the number of tokens in the messages

        Args:
            messages: List of chat completion messages

        Returns:
            Number of tokens
        """
        return sum(len(self.encoding.encode(cast(str, msg.get("content", "")))) for msg in messages)

    async def _attempt_translation(self, messages: list[ChatCompletionMessageParam], model: str) -> str:
        """
        Attempt to translate using the specified model

        Args:
            messages: List of chat completion messages
            model: Model name to use

        Returns:
            JSON string containing the translation result
        """
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=120,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "translation_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "source_lang": {
                                "type": "string",
                                "description": "The source language of the text.",
                            },
                            "translated_text": {
                                "type": "string",
                                "description": "The text after being translated.",
                            },
                        },
                        "required": ["source_lang", "translated_text"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
            stream=True,
        )
        full_content = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_content += delta.content
        return full_content

    @retry(
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((
            json.JSONDecodeError,
            ValidationError,
            ValueError,
            TimeoutError,
        )),
        reraise=True,
    )
    async def translate_sentence(self, sentence: str) -> TranslationResult:
        """
        Translate a single sentence

        Args:
            sentence: Sentence to translate

        Returns:
            Translation result containing source language and translated text
        """
        translate_query = textwrap.dedent(f"""
        Translate the following sentence to {self.target_lang}.
        Make sure your response should follow the JSON format of:
        {{"source_lang": "EN","translated_text": "Translated text"}}

        {self.additional_prompt}

        Original:
        {sentence}

        MAKE SURE TO FOLLOW THE JSON FORMAT.
        """)
        current_messages: list[ChatCompletionMessageParam] = (
            [cast(ChatCompletionMessageParam, {"role": "system", "content": self.system_prompt})]
            + self.history
            + [cast(ChatCompletionMessageParam, {"role": "user", "content": translate_query})]
        )

        # If token count exceeds the maximum, reduce conversation history
        while self.count_tokens(current_messages) > self.max_tokens:
            if len(self.history) > 1:
                self.history.pop(0)
                current_messages = (
                    [cast(ChatCompletionMessageParam, {"role": "system", "content": self.system_prompt})]
                    + self.history
                    + [cast(ChatCompletionMessageParam, {"role": "user", "content": translate_query})]
                )
            else:
                break

        last_error: Exception | None = None
        for model in self.model_names:
            try:
                response_text = await self._attempt_translation(current_messages, model)
                result: dict[str, Any] = json.loads(response_text)
                TranslationSchema.model_validate(result)
                self.history.append(
                    cast(ChatCompletionMessageParam, {"role": "assistant", "content": json.dumps(result)})
                )
                return cast(TranslationResult, result)
            except (json.JSONDecodeError, ValidationError) as e:
                self.history.append(cast(ChatCompletionMessageParam, {"role": "assistant", "content": response_text}))
                self.history.append(
                    cast(
                        ChatCompletionMessageParam,
                        {
                            "role": "user",
                            "content": "No, you should follow the JSON format of "
                            "{'source_lang': 'EN', 'translated_text': 'Translated text'}",
                        },
                    )
                )
                self.history.append(
                    cast(
                        ChatCompletionMessageParam,
                        {
                            "role": "assistant",
                            "content": "Got it. I will follow the JSON format of "
                            "{'source_lang': 'EN', 'translated_text': 'Translated text'}",
                        },
                    )
                )
                raise e
            except Exception as e:
                last_error = e
                print(f"Model {model} failed with {repr(e)}, trying next...", flush=True)
        if last_error:
            raise last_error
        raise RuntimeError("No available models")
