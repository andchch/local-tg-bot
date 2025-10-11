import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select, func, delete
from typing import List

from models import ChatMessage, Message, Base

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

    async def init_db(self):
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

    async def save_message(
        self,
        user_id: int,
        username: str,
        message_text: str
    ):
        async with self.async_session() as session:
            message = Message(
                user_id=user_id,
                username=username,
                message_text=message_text,
                timestamp=datetime.now()
            )
            session.add(message)
            await session.commit()
            logger.debug(f"Saved message from user {user_id}")

    async def get_messages_since(
        self,
        chat_id: int,
        hours: int
    ) -> List[ChatMessage]:
        since_time = datetime.now() - timedelta(hours=hours)

        async with self.async_session() as session:
            stmt = select(Message).where(
                Message.timestamp >= since_time
            ).order_by(Message.timestamp.asc())

            result = await session.execute(stmt)
            messages = result.scalars().all()

            chat_messages = [msg.to_chat_message() for msg in messages]

            logger.info(f"Retrieved {len(chat_messages)} messages from chat {chat_id} for last {hours} hours")
            return chat_messages

    async def get_message_count(self) -> int:
        async with self.async_session() as session:
            stmt = select(func.count()).select_from(Message)
            result = await session.execute(stmt)
            count = result.scalar()
            return count if count else 0

    async def cleanup_old_messages(self, days: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)

        async with self.async_session() as session:
            stmt = delete(Message).where(Message.timestamp < cutoff_date)
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()

            logger.info(f"Cleaned up {deleted_count} old messages (older than {days} days)")
            return deleted_count

    async def close(self):
        await self.async_engine.dispose()
        logger.info("Database connections closed")
