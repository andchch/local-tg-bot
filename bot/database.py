import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select, func, delete, inspect
from typing import List, Optional

from models import ChatMessage, Message, ProfanityStat, QuizScore, Base

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "data/messages.db"):
        if not db_path.startswith("sqlite"):
            db_url = f"sqlite+aiosqlite:///{db_path}"
        else:
            db_url = db_path

        self.db_url = db_url
        self.async_engine = create_async_engine(
            url=db_url,
            echo=False,  # Set to True for SQL query logging
        )
        self.async_session = async_sessionmaker(
            self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def validate_schema(self) -> bool:
        async with self.async_engine.connect() as conn:
            def check_schema(connection):
                inspector = inspect(connection)
                if not inspector.has_table('messages'):
                    return True  # Table will be created

                columns = [col['name'] for col in inspector.get_columns('messages')]
                required_columns = ['id', 'chat_id', 'user_id', 'username', 'message_text', 'timestamp']
                missing_columns = [col for col in required_columns if col not in columns]

                if missing_columns:
                    error_msg = (
                        f"\n{'='*60}\n"
                        f"❌ DATABASE SCHEMA ERROR\n"
                        f"{'='*60}\n"
                        f"Missing required columns: {', '.join(missing_columns)}\n\n"
                        f"This usually happens after updating to a new version.\n"
                        f"You need to run the migration script:\n\n"
                        f"  python scripts/migrate_add_chat_id.py\n\n"
                        f"IMPORTANT: Backup your database first:\n\n"
                        f"  python scripts/backup_db.py\n\n"
                        f"For more information, see CLAUDE.md - Database Migration section.\n"
                        f"{'='*60}\n"
                    )
                    raise RuntimeError(error_msg)

                return True

            return await conn.run_sync(check_schema)

    async def init_db(self) -> None:
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await self.validate_schema()

        logger.info("Database initialized successfully")

    async def save_message(
        self,
        user_id: int,
        username: str,
        message_text: str,
        chat_id: int,
        ts: Optional[datetime] = None
    ) -> None:
        async with self.async_session() as session:
            message = Message(
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                message_text=message_text,
                timestamp=datetime.now() if not ts else ts
            )
            session.add(message)
            await session.commit()
            logger.debug(f"Saved message from user {user_id} in chat {chat_id}")

    async def get_messages_since(
        self,
        chat_id: int,
        hours: int
    ) -> List[ChatMessage]:
        since_time = datetime.now() - timedelta(hours=hours)

        async with self.async_session() as session:
            stmt = select(Message).where(
                (Message.chat_id == chat_id) | (Message.chat_id == 0),
                Message.timestamp >= since_time
            ).order_by(Message.timestamp.asc())

            result = await session.execute(stmt)
            messages = result.scalars().all()

            chat_messages = [msg.to_chat_message() for msg in messages]

            logger.info(f"Retrieved {len(chat_messages)} messages from chat {chat_id} for last {hours} hours")
            return chat_messages

    async def get_message_count(self, chat_id: Optional[int] = None) -> int:
        async with self.async_session() as session:
            stmt = select(func.count()).select_from(Message)
            if chat_id is not None:
                stmt = stmt.where((Message.chat_id == chat_id) | (Message.chat_id == 0))
            result = await session.execute(stmt)
            count = result.scalar()
            return count if count else 0

    async def get_chat_participants(self, chat_id: int) -> List[str]:
        async with self.async_session() as session:
            stmt = select(Message.username).where(
                (Message.chat_id == chat_id) | (Message.chat_id == 0)
            ).distinct()

            result = await session.execute(stmt)
            usernames = [username for username in result.scalars().all() if username]

            logger.debug(f"Found {len(usernames)} participants in chat {chat_id}")
            return usernames

    async def update_profanity_count(
        self,
        user_id: int,
        username: str,
        chat_id: int,
        count: int
    ) -> None:
        if count == 0:
            return

        async with self.async_session() as session:
            # Try to get existing stat
            stmt = select(ProfanityStat).where(
                ProfanityStat.chat_id == chat_id,
                ProfanityStat.user_id == user_id
            )
            result = await session.execute(stmt)
            stat = result.scalar_one_or_none()

            if stat:
                # Update existing
                stat.profanity_count += count
                stat.username = username  # Update username in case it changed
                stat.last_updated = datetime.now()
            else:
                # Create new
                stat = ProfanityStat(
                    chat_id=chat_id,
                    user_id=user_id,
                    username=username,
                    profanity_count=count,
                    last_updated=datetime.now()
                )
                session.add(stat)

            await session.commit()
            logger.debug(f"Updated profanity count for user {user_id} in chat {chat_id}: +{count}")

    async def get_profanity_stats(self, chat_id: int, limit: int = 10) -> List[tuple[str, int]]:
        async with self.async_session() as session:
            stmt = select(
                ProfanityStat.username,
                ProfanityStat.profanity_count
            ).where(
                ProfanityStat.chat_id == chat_id
            ).order_by(
                ProfanityStat.profanity_count.desc()
            ).limit(limit)

            result = await session.execute(stmt)
            stats = [(username, count) for username, count in result.all()]

            logger.debug(f"Retrieved profanity stats for chat {chat_id}: {len(stats)} users")
            return stats

    async def get_user_profanity_count(self, user_id: int, chat_id: int) -> int:
        async with self.async_session() as session:
            stmt = select(ProfanityStat.profanity_count).where(
                ProfanityStat.chat_id == chat_id,
                ProfanityStat.user_id == user_id
            )
            result = await session.execute(stmt)
            count = result.scalar_one_or_none()

            return count if count else 0

    async def get_random_message_for_quiz(self, chat_id: int) -> Optional[ChatMessage]:
        async with self.async_session() as session:
            # Get messages that are long enough and not commands
            stmt = select(Message).where(
                (Message.chat_id == chat_id) | (Message.chat_id == 0),
                func.length(Message.message_text) >= 20
            ).order_by(func.random()).limit(1)

            result = await session.execute(stmt)
            message = result.scalar_one_or_none()

            if message and not message.message_text.startswith('/'):
                return message.to_chat_message()

            return None

    async def update_quiz_score(
        self,
        user_id: int,
        username: str,
        chat_id: int,
        correct: bool
    ) -> None:
        async with self.async_session() as session:
            # Try to get existing score
            stmt = select(QuizScore).where(
                QuizScore.chat_id == chat_id,
                QuizScore.user_id == user_id
            )
            result = await session.execute(stmt)
            score = result.scalar_one_or_none()

            if score:
                # Update existing
                score.total_games += 1
                if correct:
                    score.correct_answers += 1
                score.username = username  # Update username in case it changed
                score.last_played = datetime.now()
            else:
                # Create new
                score = QuizScore(
                    chat_id=chat_id,
                    user_id=user_id,
                    username=username,
                    correct_answers=1 if correct else 0,
                    total_games=1,
                    last_played=datetime.now()
                )
                session.add(score)

            await session.commit()
            logger.debug(f"Updated quiz score for user {user_id} in chat {chat_id}: correct={correct}")

    async def get_quiz_leaderboard(self, chat_id: int, limit: int = 10) -> List[tuple[str, int, int]]:
        async with self.async_session() as session:
            stmt = select(
                QuizScore.username,
                QuizScore.correct_answers,
                QuizScore.total_games
            ).where(
                QuizScore.chat_id == chat_id
            ).order_by(
                QuizScore.correct_answers.desc()
            ).limit(limit)

            result = await session.execute(stmt)
            leaderboard = [(username, correct, total) for username, correct, total in result.all()]

            logger.debug(f"Retrieved quiz leaderboard for chat {chat_id}: {len(leaderboard)} entries")
            return leaderboard

    async def cleanup_old_messages(self, days: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)

        async with self.async_session() as session:
            stmt = delete(Message).where(Message.timestamp < cutoff_date)
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()

            logger.info(f"Cleaned up {deleted_count} old messages (older than {days} days)")
            return deleted_count

    async def close(self) -> None:
        await self.async_engine.dispose()
        logger.info("Database connections closed")
