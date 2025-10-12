import os
import json
from dotenv import load_dotenv
from typing import Literal, Dict


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
    YANDEX_PROJECT_ID: str = os.getenv("YANDEX_PROJECT_ID", "")

    YANDEX_SPEECHKIT_API_KEY: str = os.getenv("YANDEX_SPEECHKIT_API_KEY", "")
    SPEECHKIT_MODEL: str = os.getenv("SPEECHKIT_MODEL", "general")
    SPEECHKIT_LANGUAGE: str = os.getenv("SPEECHKIT_LANGUAGE", "ru-RU")

    DB_PATH: str = os.getenv("DB_PATH", "data/messages.db")

    DEFAULT_SUMMARY_HOURS: int = int(os.getenv("DEFAULT_SUMMARY_HOURS", "24"))
    MAX_SUMMARY_HOURS: int = int(os.getenv("MAX_SUMMARY_HOURS", "168"))  # 7 days
    MESSAGE_CLEANUP_DAYS: int = int(os.getenv("MESSAGE_CLEANUP_DAYS", "30"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Access control
    KNOWN_USERS_JSON: str = os.getenv("KNOWN_USERS", "{}")
    ALLOWED_CHAT_IDS: str = os.getenv("ALLOWED_CHAT_IDS", "")

    @classmethod
    def get_known_users(cls) -> Dict[int, str]:
        try:
            users_dict = json.loads(cls.KNOWN_USERS_JSON)
            return {int(k): v for k, v in users_dict.items()}
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid KNOWN_USERS JSON format: {e}")

    @classmethod
    def get_allowed_chat_ids(cls) -> tuple:
        if not cls.ALLOWED_CHAT_IDS:
            return ()
        try:
            return tuple(int(chat_id.strip()) for chat_id in cls.ALLOWED_CHAT_IDS.split(',') if chat_id.strip())
        except ValueError as e:
            raise ValueError(f"Invalid ALLOWED_CHAT_IDS format: {e}")

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

        if not cls.YANDEX_SPEECHKIT_API_KEY:
            raise ValueError("YANDEX_SPEECHKIT_API_KEY is not set in environment variables")

        cls.get_known_users()
        cls.get_allowed_chat_ids()

        return True
