from datetime import datetime
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
import httpx
import random

from messages import Messages
from database import Database
from summarizer import Summarizer
from transcription import Transcriber
from config import Config
from consts import KNOWN_USERS, ALLOWED_CHAT_ID, tags, h_m

logger = logging.getLogger(__name__)

router = Router()

db = Database(Config.DB_PATH)
summarizer = Summarizer()
transcriber = Transcriber()


def is_access_allowed(message: Message) -> bool:
    return abs(message.chat.id) in ALLOWED_CHAT_ID or abs(message.chat.id) in KNOWN_USERS.keys()


def get_username(message: Message) -> str:
    if message.from_user.id in KNOWN_USERS.keys():
        return KNOWN_USERS[message.from_user.id]
    if message.from_user.username:
        return message.from_user.username
    return f"User{message.from_user.id}"


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

    await message.answer(Messages.welcome())


@router.message(Command("summary"))
async def cmd_summary(message: Message):
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

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

        if len(messages) < 30:
            await processing_msg.delete()
            await message.answer(Messages.error_not_enough_msgs(len(messages)))
            return

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
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

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
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

    if message.chat.type not in ["group", "supergroup"]:
        if h_m.intersection(set(message.text)):
            await random_shit(message, True)
            return
        else:
            await random_shit(message)
            return

    if message.text and message.text.startswith("/"):
        return

    if not message.text or not message.text.strip():
        return

    try:
        username = get_username(message)
        ts = datetime.now()

        await db.save_message(
            user_id=message.from_user.id,
            message_text=message.text,
            username=username,
            ts=ts
        )

        logger.debug(f"Saved message from {message.from_user.id} ({username}) in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
        
        
@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

    if message.chat.type not in ["group", "supergroup"]:
        await random_shit(message)
        return

    try:
        username = get_username(message)
        ts = datetime.now()

        audio_file = await bot.download(message.voice.file_id)

        text = await transcriber.transcribe_audio(audio_file)

        if text:
            await db.save_message(
                user_id=message.from_user.id,
                message_text=text,
                username=username,
                ts=ts
            )
            logger.debug(f"Saved transcribed audio message from {message.from_user.id} ({username}) in chat {message.chat.id}")
        else:
            logger.warning(f"Failed to transcribe audio from {message.from_user.id} in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error processing voice message: {e}", exc_info=True)


@router.message(F.video_note)
async def handle_video_note(message: Message, bot: Bot):
    if not is_access_allowed(message):
        await message.answer(Messages.error_not_allowed_chat())
        return

    if message.chat.type not in ["group", "supergroup"]:
        await random_shit(message)
        return

    try:
        username = get_username(message)
        ts = datetime.now()

        video_file = await bot.download(message.video_note.file_id)

        text = await transcriber.transcribe_video_note(video_file)

        if text:
            await db.save_message(
                user_id=message.from_user.id,
                message_text=text,
                username=username,
                ts=ts
            )
            logger.debug(f"Saved transcribed circle message from {message.from_user.id} ({username}) in chat {message.chat.id}")
        else:
            logger.warning(f"Failed to transcribe video note from {message.from_user.id} in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error processing video note: {e}", exc_info=True)
        
        
async def random_shit(message: Message, nsfw: bool = False):
    if nsfw:
        content_type = "nsfw"
    else:
        content_type = "sfw"

    cat = random.choice(tags[content_type])

    async with httpx.AsyncClient() as client:
        r = await client.get(f'https://api.waifu.pics/{content_type}/{cat}')

        if r.status_code == 200:
            data = r.json()
            image_url = data.get('url')
            await message.answer_photo(photo=image_url)
        else:
            await message.answer("Zzz 😴😴😴")