"""Unit tests for messages module."""

import pytest
from bot.messages import Messages


class TestMessages:
    """Test Messages class."""

    def test_welcome(self):
        """Test welcome message."""
        msg = Messages.welcome()
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_stats(self):
        """Test stats message formatting."""
        msg = Messages.stats(10, 50, 100)
        assert "10" in msg
        assert "50" in msg
        assert "100" in msg

    def test_summary_header(self):
        """Test summary header formatting."""
        msg = Messages.summary_header(24)
        assert "24" in msg

    def test_processing_summary(self):
        """Test processing message."""
        msg = Messages.processing_summary(12)
        assert "12" in msg

    def test_error_max_hours_exceeded(self):
        """Test max hours error message."""
        msg = Messages.error_max_hours_exceeded(168)
        assert "168" in msg

    def test_error_summary_generation(self):
        """Test error message formatting."""
        error_msg = "API connection failed"
        msg = Messages.error_summary_generation(error_msg)
        assert error_msg in msg

    def test_error_not_enough_msgs(self):
        """Test not enough messages error."""
        msg = Messages.error_not_enough_msgs(15)
        assert "15" in msg

    def test_no_messages(self):
        """Test no messages info."""
        msg = Messages.no_messages(6)
        assert "6" in msg

    def test_ai_system_prompt(self):
        """Test AI system prompt generation."""
        prompt = Messages.ai_system_prompt(24)
        assert "24" in prompt
        assert len(prompt) > 100  # Should be a substantial prompt

    def test_ai_empty_response_error(self):
        """Test AI empty response error."""
        msg = Messages.ai_empty_response_error("openai")
        assert "openai" in msg.lower()

    def test_ai_unknown_provider_error(self):
        """Test unknown provider error."""
        msg = Messages.ai_unknown_provider_error("invalid_provider")
        assert "invalid_provider" in msg
