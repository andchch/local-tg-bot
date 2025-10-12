import asyncio
import logging
import sys
from typing import Any, Callable, Dict, Awaitable
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject

from config import Config
from database import Database
from summarizer import Summarizer
from transcription import Transcriber
from handlers import router


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


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


async def on_startup(bot: Bot, db: Database) -> None:
    logger.info("Starting bot...")

    await db.init_db()
    bot_info = await bot.get_me()

    logger.info(f"Bot started: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"AI Provider: {Config.AI_PROVIDER}")
    logger.info(f"Database: {Config.DB_PATH}")
    logger.info(f"Default summary hours: {Config.DEFAULT_SUMMARY_HOURS}")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Shutting down bot...")
    await bot.session.close()


async def main() -> None:
    try:
        Config.validate()

        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )

        db = Database(Config.DB_PATH)
        summarizer = Summarizer()
        transcriber = Transcriber()

        dp = Dispatcher()

        allowed_users = set(Config.get_known_users().keys())
        allowed_chats = set(Config.get_allowed_chat_ids())
        dp.message.middleware(AccessControlMiddleware(allowed_users, allowed_chats))

        dp.message.middleware(DependencyInjectionMiddleware(db, summarizer, transcriber))

        dp.include_router(router)

        await on_startup(bot, db)

        async def periodic_cleanup():
            while True:
                try:
                    await asyncio.sleep(86400)  # 24 часа
                    logger.info("Running periodic message cleanup...")
                    deleted = await db.cleanup_old_messages(Config.MESSAGE_CLEANUP_DAYS)
                    logger.info(f"Cleanup completed: {deleted} messages deleted")
                except Exception as e:
                    logger.error(f"Error in periodic cleanup: {e}", exc_info=True)
        cleanup_task = asyncio.create_task(periodic_cleanup())

        try:
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

        except KeyboardInterrupt:
            logger.info("Received stop signal")

        finally:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
            await on_shutdown(bot)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
