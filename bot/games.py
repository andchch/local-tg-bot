import random
from typing import List, Tuple
from models import ChatMessage


def create_quiz_question(
    message: ChatMessage,
    all_participants: List[str]
) -> Tuple[str, List[str], str]:
    correct_answer = message.get_display_name()

    wrong_answers = [p for p in all_participants if p != correct_answer]

    if len(wrong_answers) < 3:
        while len(wrong_answers) < 3:
            wrong_answers.append(f"User{random.randint(1000, 9999)}")

    wrong_answers = random.sample(wrong_answers, min(3, len(wrong_answers)))

    options = wrong_answers + [correct_answer]
    random.shuffle(options)

    date_str = message.timestamp.strftime("%d.%m.%Y %H:%M")
    question_text = f"💬 _{message.message_text}_\n\n🗓 Дата: {date_str}\n\n❓ **Кто это сказал?**"

    return question_text, options, correct_answer
