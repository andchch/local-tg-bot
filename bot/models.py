from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import String, Integer, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
    )

    def to_chat_message(self) -> "ChatMessage":
        return ChatMessage(
            user_id=self.user_id,
            username=self.username,
            message_text=self.message_text,
            timestamp=self.timestamp
        )


class ChatMessage:
    def __init__(
        self,
        user_id: int,
        message_text: str,
        timestamp: datetime,
        username: Optional[str] = None
    ):
        self.user_id = user_id
        self.username = username
        self.message_text = message_text
        self.timestamp = timestamp

    def get_display_name(self) -> str:
        return f"@{self.username}"
        

    def format_for_summary(self) -> str:
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M")
        display_name = self.get_display_name()
        return f"[{time_str}] {display_name}: {self.message_text}"

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatMessage":
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()

        return cls(
            user_id=data['user_id'],
            message_text=data['message_text'],
            timestamp=timestamp,
            username=data.get('username')
        )

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'message_text': self.message_text,
            'timestamp': self.timestamp,
        }

    def __str__(self) -> str:
        return self.format_for_summary()

    def __repr__(self) -> str:
        return f"ChatMessage(user_id={self.user_id}, text='{self.message_text[:30]}...', timestamp={self.timestamp})"
