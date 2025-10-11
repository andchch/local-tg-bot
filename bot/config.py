import os
from dotenv import load_dotenv
from typing import Literal


load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    AI_PROVIDER: Literal["openai", "anthropic", "yagpt"] = os.getenv("AI_PROVIDER", "openai")  # type: ignore
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY", "")
    
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    YANDEX_MODEL: str = os.getenv("YANDEX_MODEL", "")

    DB_PATH: str = os.getenv("DB_PATH", "data/messages.db")

    DEFAULT_SUMMARY_HOURS: int = int(os.getenv("DEFAULT_SUMMARY_HOURS", "24"))
    MAX_SUMMARY_HOURS: int = int(os.getenv("MAX_SUMMARY_HOURS", "168"))  # 7 days
    MESSAGE_CLEANUP_DAYS: int = int(os.getenv("MESSAGE_CLEANUP_DAYS", "30"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in environment variables")

        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set for OpenAI provider")

        if cls.AI_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set for Anthropic provider")
        
        if cls.AI_PROVIDER == "yagpt" and not cls.YANDEX_API_KEY:
            raise ValueError("YANDEX_API_KEY is not set for Yandex provider")

        if cls.AI_PROVIDER not in ["openai", "anthropic", "yagpt"]:
            raise ValueError(f"Invalid AI_PROVIDER: {cls.AI_PROVIDER}. Must be 'openai' or 'anthropic' or 'yagpt'")

        return True

Config.validate()
