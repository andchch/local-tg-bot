"""Unit tests for models module."""

import pytest
from datetime import datetime
from bot.models import ChatMessage


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_creation(self):
        """Test creating a ChatMessage instance."""
        msg = ChatMessage(
            user_id=123,
            message_text="Hello world",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            username="TestUser",
            chat_id=456
        )
        assert msg.user_id == 123
        assert msg.message_text == "Hello world"
        assert msg.username == "TestUser"
        assert msg.chat_id == 456

    def test_get_display_name_with_username(self):
        """Test get_display_name when username is provided."""
        msg = ChatMessage(
            user_id=123,
            message_text="Test",
            timestamp=datetime.now(),
            username="JohnDoe"
        )
        assert msg.get_display_name() == "JohnDoe"

    def test_get_display_name_without_username(self):
        """Test get_display_name when username is None."""
        msg = ChatMessage(
            user_id=123,
            message_text="Test",
            timestamp=datetime.now(),
            username=None
        )
        assert msg.get_display_name() == "User123"

    def test_format_for_summary(self):
        """Test format_for_summary method."""
        msg = ChatMessage(
            user_id=123,
            message_text="Hello world",
            timestamp=datetime(2025, 1, 1, 12, 30, 45),
            username="Alice"
        )
        formatted = msg.format_for_summary()
        assert "[2025-01-01 12:30:45]" in formatted
        assert "Alice" in formatted
        assert "Hello world" in formatted

    def test_to_dict(self):
        """Test to_dict method."""
        msg = ChatMessage(
            user_id=123,
            message_text="Test message",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            username="Bob",
            chat_id=789
        )
        msg_dict = msg.to_dict()
        assert msg_dict["user_id"] == 123
        assert msg_dict["message_text"] == "Test message"
        assert msg_dict["username"] == "Bob"
        assert msg_dict["chat_id"] == 789

    def test_from_dict(self):
        """Test from_dict classmethod."""
        data = {
            "user_id": 123,
            "message_text": "Test",
            "timestamp": "2025-01-01T12:00:00",
            "username": "Charlie",
            "chat_id": 999
        }
        msg = ChatMessage.from_dict(data)
        assert msg.user_id == 123
        assert msg.message_text == "Test"
        assert msg.username == "Charlie"
        assert msg.chat_id == 999

    def test_str_representation(self):
        """Test string representation."""
        msg = ChatMessage(
            user_id=123,
            message_text="Test",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            username="Dave"
        )
        str_repr = str(msg)
        assert "Dave" in str_repr
        assert "Test" in str_repr
