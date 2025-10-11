import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from messages import Messages
from database import Database
from summarizer import Summarizer
from config import Config
from users import KNOWN_USERS

logger = logging.getLogger(__name__)

router = Router()

db = Database(Config.DB_PATH)
summarizer = Summarizer()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(Messages.welcome())


@router.message(Command("summary"))
async def cmd_summary(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) > 1:
            hours = int(command_parts[1])
        else:
            hours = Config.DEFAULT_SUMMARY_HOURS

        if hours <= 0:
            await message.answer(Messages.error_invalid_hours())
            return

        if hours > Config.MAX_SUMMARY_HOURS:
            await message.answer(Messages.error_max_hours_exceeded(Config.MAX_SUMMARY_HOURS))
            return

    except ValueError:
        await message.answer(Messages.error_invalid_format())
        return

    processing_msg = await message.answer(Messages.processing_summary(hours))

    try:
        messages = await db.get_messages_since(message.chat.id, hours)
        summary = await summarizer.summarize(messages, hours)
        result_text = Messages.summary_header(hours) + summary
        
        await processing_msg.delete()

        await message.answer(result_text, parse_mode="Markdown")
        
        logger.info(f"Summary generated for chat {message.chat.id} ({len(messages)} messages, {hours} hours)")

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        await processing_msg.edit_text(Messages.error_summary_generation(str(e)))


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        messages_24h = await db.get_messages_since(message.chat.id, 24)
        messages_7d = await db.get_messages_since(message.chat.id, 168)  # 7 days
        total_messages = await db.get_message_count(message.chat.id)

        stats_text = Messages.stats(len(messages_24h), len(messages_7d), total_messages)
        await message.answer(stats_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        await message.answer(Messages.error_stats_retrieval(str(e)))


@router.message(F.text)
async def handle_message(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    if message.text and message.text.startswith("/"):
        return

    if not message.text or not message.text.strip():
        return

    try:
        username = KNOWN_USERS.get(message.from_user.id, message.from_user.username)

        await db.save_message(
            user_id=message.from_user.id,
            message_text=message.text,
            username=username
        )

        logger.debug(f"Saved message from {message.from_user.id} ({username}) in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
