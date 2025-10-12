"""
Bot messages and text templates.
Centralized message management for easy localization and maintenance.
"""


class Messages:
    """Collection of all bot messages and text templates."""

    # ==================== Commands ====================

    @staticmethod
    def welcome() -> str:
        """Welcome message for /start command."""
        return """👋 Привет!"""

    @staticmethod
    def stats(messages_24h: int, messages_7d: int, total: int) -> str:
        """
        Statistics message.

        Args:
            messages_24h: Number of messages in last 24 hours
            messages_7d: Number of messages in last 7 days
            total: Total number of saved messages
        """
        return f"""📈 **Статистика сообщений в чате**

За последние 24 часа: {messages_24h} сообщений
За последние 7 дней: {messages_7d} сообщений
Всего сохранено: {total} сообщений"""

    @staticmethod
    def summary_header(hours: int) -> str:
        """
        Summary header.

        Args:
            hours: Number of hours covered by summary
        """
        return f"📊 **Саммари разговора за последние {hours} часов**\n\n"

    @staticmethod
    def processing_summary(hours: int) -> str:
        """
        Processing message while generating summary.

        Args:
            hours: Number of hours being processed
        """
        return f"⏳ Генерирую резюме за последние {hours} часов..."

    # ==================== Errors ====================

    @staticmethod
    def error_group_only() -> str:
        """Error when command is used outside of group."""
        return "❌ Эта команда работает только в группах!"

    @staticmethod
    def error_invalid_hours() -> str:
        """Error for invalid hours parameter."""
        return "❌ Количество часов должно быть положительным числом!"

    @staticmethod
    def error_max_hours_exceeded(max_hours: int) -> str:
        """
        Error when requested hours exceed maximum.

        Args:
            max_hours: Maximum allowed hours
        """
        days = max_hours // 24
        return f"❌ Максимальный период для саммари - {max_hours} часов ({days} дней)"

    @staticmethod
    def error_invalid_format() -> str:
        """Error for invalid command format."""
        return "❌ Неверный формат! Используйте: /summary [часы]\nПример: /summary 24"

    @staticmethod
    def error_summary_generation(error: str) -> str:
        """
        Error during summary generation.

        Args:
            error: Error message
        """
        return f"❌ Ошибка при генерации саммари: {error}"

    @staticmethod
    def error_stats_retrieval(error: str) -> str:
        """
        Error during stats retrieval.

        Args:
            error: Error message
        """
        return f"❌ Ошибка при получении статистики: {error}"
    
    @staticmethod
    def error_not_enough_msgs(mc: int) -> str:
        return f"❌ Йоу бро, {mc} сообщений можно и самому прочитать"
    
    @staticmethod
    def error_not_allowed_chat() -> str:
        return f"❌ Sosi"

    # ==================== Info ====================

    @staticmethod
    def no_messages(hours: int) -> str:
        """
        Message when no messages found for period.

        Args:
            hours: Number of hours checked
        """
        return f"📭 За последние {hours} часов не было сообщений в этом чате."

    # ==================== AI Prompts ====================

    @staticmethod
    def ai_system_prompt(hours: int) -> str:
        """
        System prompt for AI summarization.

        Args:
            hours: Number of hours covered by messages
        """
        return f"""Ты - ассистент для анализа групповых разговоров в Telegram.
Твоя задача - создать краткое, но содержательное резюме разговора.

Пожалуйста, создай структурированное резюме на русском языке, которое включает:

1. **Основные темы**: Какие темы обсуждались?
2. **Ключевые моменты**: Самые важные высказывания или решения
3. **Активные участники**: Кто больше всего участвовал в обсуждении
4. **Итоги**: Краткие выводы по итогам разговора

Будь кратким и по делу. Резюме должно быть информативным, но не слишком длинным.

Разговор за последние {hours} часов:"""

    @staticmethod
    def ai_empty_response_error(provider: str) -> str:
        """
        Error when AI returns empty response.

        Args:
            provider: AI provider name (openai, anthropic)
        """
        return f"{provider.upper()} returned empty response"

    @staticmethod
    def ai_unknown_provider_error(provider: str) -> str:
        """
        Error for unknown AI provider.

        Args:
            provider: Unknown provider name
        """
        return f"Unknown AI provider: {provider}"
