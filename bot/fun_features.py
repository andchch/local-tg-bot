import random
from typing import List, Tuple
from messages import Messages


def magic_ball() -> str:
    answers = Messages.magic_ball_answers()
    return random.choice(answers)


def pick_random_person(participants: List[str]) -> str:
    if not participants:
        return "Никого нет в списке участников! 👻"

    return random.choice(participants)


def rate_text(text: str) -> Tuple[int, str]:
    # Use text hash as seed for consistency
    seed = hash(text) % (2**32)
    rng = random.Random(seed)

    score = rng.randint(1, 10)

    comments_dict = Messages.rating_comments()
    if score <= 3:
        comment = rng.choice(comments_dict["1-3"])
    elif score <= 6:
        comment = rng.choice(comments_dict["4-6"])
    elif score <= 8:
        comment = rng.choice(comments_dict["7-8"])
    else:
        comment = rng.choice(comments_dict["9-10"])

    return score, comment
