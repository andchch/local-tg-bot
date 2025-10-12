import logging
from typing import List, Optional

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import Config
from messages import Messages
from models import ChatMessage

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self) -> None:
        self.provider = Config.AI_PROVIDER

        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
            logger.info(f"Initialized OpenAI client with model: {self.model}")

        elif self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.ANTHROPIC_MODEL
            logger.info(f"Initialized Anthropic client with model: {self.model}")
            
        elif self.provider == "yagpt":
            self.client = AsyncOpenAI(
                api_key=Config.YANDEX_API_KEY,
                base_url="https://llm.api.cloud.yandex.net/v1",
                project=Config.YANDEX_PROJECT_ID
            )
            self.model = Config.YANDEX_MODEL
            logger.info(f"Initialized Yandex client with model: {self.model}")

    def _format_messages(self, messages: List[ChatMessage]) -> str:
        if not messages:
            return ""

        formatted_lines = [msg.format_for_summary() for msg in messages]
        return "\n".join(formatted_lines)

    def _create_prompt(self, formatted_messages: str, hours: int) -> str:
        system_prompt = Messages.ai_system_prompt(hours)
        return f"{system_prompt}\n\n{formatted_messages}"

    async def summarize(self, messages: List[ChatMessage], hours: int) -> str:
        if not messages:
            return Messages.no_messages(hours)

        formatted_messages = self._format_messages(messages)
        prompt = self._create_prompt(formatted_messages, hours)

        logger.info(f"Generating summary for {len(messages)} messages using {self.provider}")

        try:
            if self.provider == "openai" or self.provider == "yagpt":
                return await self._summarize_openai(prompt)
            elif self.provider == "anthropic":
                return await self._summarize_anthropic(prompt)
            else:
                raise ValueError(Messages.ai_unknown_provider_error(self.provider))

        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return Messages.error_summary_generation(str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _summarize_openai(self, prompt: str) -> str:
        logger.debug("Calling OpenAI API for summary generation")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        summary = response.choices[0].message.content
        if not summary:
            raise ValueError(Messages.ai_empty_response_error("openai"))

        logger.info(f"OpenAI summary generated successfully (tokens: {response.usage.total_tokens})")
        return summary

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _summarize_anthropic(self, prompt: str) -> str:
        logger.debug("Calling Anthropic API for summary generation")
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        if not response.content:
            raise ValueError(Messages.ai_empty_response_error("anthropic"))

        summary = response.content[0].text
        logger.info(f"Anthropic summary generated successfully (tokens: {response.usage.input_tokens + response.usage.output_tokens})")
        return summary
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _summarize_yagpt(self, prompt: str) -> str:
        logger.debug("Calling Yandex GPT API for summary generation")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        summary = response.choices[0].message.content
        if not summary:
            raise ValueError(Messages.ai_empty_response_error("yagpt"))

        logger.info(f"YaGPT summary generated successfully (tokens: {response.usage.total_tokens})")
        return summary
