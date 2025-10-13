from datetime import datetime
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from messages import Messages
from database import Database
from summarizer import Summarizer
from transcription import Transcriber
from config import Config
from consts import NSFW_EMOJI_TRIGGERS
from fun_features import magic_ball, pick_random_person, rate_text, send_anime_image
from profanity import count_profanity, get_toxicity_title
from games import create_quiz_question

logger = logging.getLogger(__name__)

router = Router()

KNOWN_USERS = Config.get_known_users()


def get_username(message: Message) -> str:
    if message.from_user.id in KNOWN_USERS:
        return KNOWN_USERS[message.from_user.id]
    if message.from_user.username:
        return message.from_user.username
    return f"User{message.from_user.id}"


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(Messages.welcome())


@router.message(Command("ball"))
async def cmd_ball(message: Message) -> None:
    answer = magic_ball()
    await message.answer(f"🔮 {answer}")


@router.message(Command("who"))
async def cmd_who(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    participants = await db.get_chat_participants(message.chat.id)
    chosen = pick_random_person(participants)

    command_parts = message.text.split(maxsplit=1)
    question = command_parts[1] if len(command_parts) > 1 else ""

    if question:
        await message.answer(f"🎲 {question}\n\n👉 **{chosen}**")
    else:
        await message.answer(f"🎲 Выбран: **{chosen}**")


@router.message(Command("rate"))
async def cmd_rate(message: Message) -> None:
    if message.reply_to_message and message.reply_to_message.text:
        text_to_rate = message.reply_to_message.text
    else:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            await message.answer("❌ Используйте: `/rate <текст>` или ответьте на сообщение командой `/rate`")
            return
        text_to_rate = command_parts[1]

    score, comment = rate_text(text_to_rate)

    response = f"⭐️ **Оценка: {score}/10**\n💬 _{comment}_"
    await message.answer(response, parse_mode="Markdown")


@router.message(Command("tox"))
async def cmd_toxicity(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        stats = await db.get_profanity_stats(message.chat.id, limit=10)

        if not stats:
            await message.answer("📊 В этом чате еще нет статистики по токсичности!")
            return

        response = "🤬 **Топ самых токсичных участников:**\n\n"
        for i, (username, count) in enumerate(stats, 1):
            title = get_toxicity_title(count)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            response += f"{medal} **{username}**: {count} раз — _{title}_\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error getting toxicity stats: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при получении статистики: {e}")


@router.message(Command("mytox"))
async def cmd_mytoxicity(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        count = await db.get_user_profanity_count(
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )

        title = get_toxicity_title(count)
        username = get_username(message)

        response = f"📊 **Твоя статистика токсичности:**\n\n"
        response += f"👤 {username}\n"
        response += f"💬 Использовано мата: **{count}** раз\n"
        response += f"🏆 Звание: **{title}**"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error getting user toxicity: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при получении статистики: {e}")


@router.message(Command("whosaid"))
async def cmd_whosaid(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        quiz_message = await db.get_random_message_for_quiz(message.chat.id)

        if not quiz_message:
            await message.answer("❌ Недостаточно сообщений для викторины! Нужно минимум 4 участника с сообщениями длиннее 20 символов.")
            return

        participants = await db.get_chat_participants(message.chat.id)

        if len(participants) < 4:
            await message.answer("❌ Недостаточно участников для викторины! Нужно минимум 4 участника.")
            return

        question_text, options, correct_answer = create_quiz_question(quiz_message, participants)

        keyboard = []
        for option in options:
            # Use callback_data format: quiz:<chat_id>:<correct_answer>:<selected_answer>
            callback_data = f"quiz:{message.chat.id}:{correct_answer}:{option}"
            keyboard.append([InlineKeyboardButton(text=option, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(question_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error creating quiz: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при создании викторины: {e}")


@router.callback_query(F.data.startswith("quiz:"))
async def handle_quiz_answer(callback: CallbackQuery, db: Database) -> None:
    try:
        # Parse callback data: quiz:<chat_id>:<correct_answer>:<selected_answer>
        parts = callback.data.split(":", 3)
        if len(parts) != 4:
            await callback.answer("❌ Ошибка данных")
            return

        _, chat_id_str, correct_answer, selected_answer = parts
        chat_id = int(chat_id_str)

        is_correct = selected_answer == correct_answer

        if callback.from_user.id in KNOWN_USERS:
            username = KNOWN_USERS[callback.from_user.id]
        elif callback.from_user.username:
            username = callback.from_user.username
        else:
            username = f"User{callback.from_user.id}"

        await db.update_quiz_score(
            user_id=callback.from_user.id,
            username=username,
            chat_id=chat_id,
            correct=is_correct
        )

        if is_correct:
            response = f"✅ **{username}** угадал правильно! Это действительно сказал **{correct_answer}**! 🎉"
        else:
            response = f"❌ **{username}** ошибся! Правильный ответ: **{correct_answer}**"

        await callback.message.edit_text(
            f"{callback.message.text}\n\n{response}",
            parse_mode="Markdown"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling quiz answer: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при обработке ответа")


@router.message(Command("quizstats"))
async def cmd_quizstats(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(Messages.error_group_only())
        return

    try:
        leaderboard = await db.get_quiz_leaderboard(message.chat.id, limit=10)

        if not leaderboard:
            await message.answer("📊 Еще никто не играл в викторину в этом чате!")
            return

        response = "🏆 **Топ знатоков чата:**\n\n"
        for i, (username, correct, total) in enumerate(leaderboard, 1):
            accuracy = (correct / total * 100) if total > 0 else 0
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            response += f"{medal} **{username}**: {correct}/{total} ({accuracy:.1f}%)\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error getting quiz stats: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при получении статистики: {e}")


@router.message(Command("summary"))
async def cmd_summary(message: Message, db: Database, summarizer: Summarizer) -> None:
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
async def cmd_stats(message: Message, db: Database) -> None:
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
async def handle_message(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        if NSFW_EMOJI_TRIGGERS.intersection(set(message.text)):
            await send_anime_image(message, nsfw=True)
            return
        else:
            await send_anime_image(message, nsfw=False)
            return

    if message.text and message.text.startswith("/"):
        return

    if not message.text or not message.text.strip():
        return

    try:
        if message.forward_from:
            if message.forward_from.id in KNOWN_USERS.keys():
                username = KNOWN_USERS[message.forward_from.id]
            elif message.forward_from.first_name:
                username = message.forward_from.first_name
            else:
                username = message.forward_from.username

            ts = datetime.now()

            text = f'{KNOWN_USERS[message.from_user.id]} переслал сообщение от {username} c текстом: {message.text}'

            await db.save_message(
                user_id=message.forward_from.id,
                message_text=text,
                username=username,
                chat_id=message.chat.id,
                ts=ts
            )

        else:
            username = get_username(message)
            ts = datetime.now()

            await db.save_message(
                user_id=message.from_user.id,
                message_text=message.text,
                username=username,
                chat_id=message.chat.id,
                ts=ts
            )

            profanity_count = count_profanity(message.text)
            if profanity_count > 0:
                await db.update_profanity_count(
                    user_id=message.from_user.id,
                    username=username,
                    chat_id=message.chat.id,
                    count=profanity_count
                )

            logger.debug(f"Saved message from {message.from_user.id} ({username}) in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
        
        
@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot, db: Database, transcriber: Transcriber) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await send_anime_image(message)
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
                chat_id=message.chat.id,
                ts=ts
            )

            profanity_count = count_profanity(text)
            if profanity_count > 0:
                await db.update_profanity_count(
                    user_id=message.from_user.id,
                    username=username,
                    chat_id=message.chat.id,
                    count=profanity_count
                )
            logger.debug(f"Saved transcribed audio message from {message.from_user.id} ({username}) in chat {message.chat.id}")
        else:
            logger.warning(f"Failed to transcribe audio from {message.from_user.id} in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error processing voice message: {e}", exc_info=True)


@router.message(F.video_note)
async def handle_video_note(message: Message, bot: Bot, db: Database, transcriber: Transcriber) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await send_anime_image(message)
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
                chat_id=message.chat.id,
                ts=ts
            )

            profanity_count = count_profanity(text)
            if profanity_count > 0:
                await db.update_profanity_count(
                    user_id=message.from_user.id,
                    username=username,
                    chat_id=message.chat.id,
                    count=profanity_count
                )
            logger.debug(f"Saved transcribed circle message from {message.from_user.id} ({username}) in chat {message.chat.id}")
        else:
            logger.warning(f"Failed to transcribe video note from {message.from_user.id} in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"Error processing video note: {e}", exc_info=True)


@router.message(F.photo)
async def handle_photo(message: Message, db: Database) -> None:
    if message.chat.type not in ["group", "supergroup"]:
        await send_anime_image(message)
        return
    try:
        username = get_username(message)
        ts = datetime.now()

        await db.save_message(
            user_id=message.from_user.id,
            message_text="(прислал какое-то изображение)",
            username=username,
            chat_id=message.chat.id,
            ts=ts
        )

    except Exception as e:
        logger.error(f"Error processing photo: {e}", exc_info=True)