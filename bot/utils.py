from aiogram import BaseMiddleware
from typing import Any, Callable, Dict, Awaitable
from aiogram.types import TelegramObject

from transcription import Transcriber
from database import Database
from summarizer import Summarizer


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, allowed_users: set, allowed_chats: set):
        super().__init__()
        self.allowed_users = allowed_users
        self.allowed_chats = allowed_chats

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        from aiogram.types import Message
        from messages import Messages

        if isinstance(event, Message):
            chat_id = abs(event.chat.id)
            user_id = event.from_user.id if event.from_user else None

            if chat_id not in self.allowed_chats and user_id not in self.allowed_users:
                await event.answer(Messages.error_not_allowed_chat())
                return  # Block further processing

        return await handler(event, data)


class DependencyInjectionMiddleware(BaseMiddleware):
    def __init__(self, db: Database, summarizer: Summarizer, transcriber: Transcriber):
        super().__init__()
        self.db = db
        self.summarizer = summarizer
        self.transcriber = transcriber

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["db"] = self.db
        data["summarizer"] = self.summarizer
        data["transcriber"] = self.transcriber
        return await handler(event, data)
