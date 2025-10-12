"""Unit tests for config module."""

import pytest
import os
from unittest.mock import patch
from bot.config import Config


class TestConfig:
    """Test Config class."""

    def test_get_known_users_valid_json(self):
        """Test parsing valid KNOWN_USERS JSON."""
        with patch.dict(os.environ, {"KNOWN_USERS": '{"123": "Alice", "456": "Bob"}'}):
            # Reload config
            Config.KNOWN_USERS_JSON = os.getenv("KNOWN_USERS", "{}")
            users = Config.get_known_users()
            assert users == {123: "Alice", 456: "Bob"}

    def test_get_known_users_empty(self):
        """Test parsing empty KNOWN_USERS."""
        with patch.dict(os.environ, {"KNOWN_USERS": "{}"}):
            Config.KNOWN_USERS_JSON = os.getenv("KNOWN_USERS", "{}")
            users = Config.get_known_users()
            assert users == {}

    def test_get_known_users_invalid_json(self):
        """Test parsing invalid KNOWN_USERS JSON."""
        with patch.dict(os.environ, {"KNOWN_USERS": "invalid json"}):
            Config.KNOWN_USERS_JSON = os.getenv("KNOWN_USERS", "{}")
            with pytest.raises(ValueError, match="Invalid KNOWN_USERS JSON format"):
                Config.get_known_users()

    def test_get_allowed_chat_ids_valid(self):
        """Test parsing valid ALLOWED_CHAT_IDS."""
        with patch.dict(os.environ, {"ALLOWED_CHAT_IDS": "123,456,789"}):
            Config.ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "")
            chat_ids = Config.get_allowed_chat_ids()
            assert chat_ids == (123, 456, 789)

    def test_get_allowed_chat_ids_empty(self):
        """Test parsing empty ALLOWED_CHAT_IDS."""
        with patch.dict(os.environ, {"ALLOWED_CHAT_IDS": ""}):
            Config.ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "")
            chat_ids = Config.get_allowed_chat_ids()
            assert chat_ids == ()

    def test_get_allowed_chat_ids_with_spaces(self):
        """Test parsing ALLOWED_CHAT_IDS with spaces."""
        with patch.dict(os.environ, {"ALLOWED_CHAT_IDS": " 111 , 222 , 333 "}):
            Config.ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "")
            chat_ids = Config.get_allowed_chat_ids()
            assert chat_ids == (111, 222, 333)

    def test_get_allowed_chat_ids_invalid(self):
        """Test parsing invalid ALLOWED_CHAT_IDS."""
        with patch.dict(os.environ, {"ALLOWED_CHAT_IDS": "123,abc,456"}):
            Config.ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "")
            with pytest.raises(ValueError, match="Invalid ALLOWED_CHAT_IDS format"):
                Config.get_allowed_chat_ids()
