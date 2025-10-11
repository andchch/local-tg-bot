import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database import Database
from handlers import router


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, db: Database):
    logger.info("Starting bot...")

    await db.init_db()
    bot_info = await bot.get_me()
    
    logger.info(f"Bot started: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"AI Provider: {Config.AI_PROVIDER}")
    logger.info(f"Database: {Config.DB_PATH}")
    logger.info(f"Default summary hours: {Config.DEFAULT_SUMMARY_HOURS}")


async def on_shutdown(bot: Bot):
    logger.info("Shutting down bot...")
    await bot.session.close()


async def main():
    try:
        Config.validate()

        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )

        dp = Dispatcher()
        dp.include_router(router)
        db = Database(Config.DB_PATH)

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
