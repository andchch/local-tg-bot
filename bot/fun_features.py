import random
from typing import List, Tuple
import logging
import httpx
from aiogram.types import Message

from messages import Messages
from consts import ANIME_TAGS

logger = logging.getLogger(__name__)

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


async def send_anime_image(message: Message, nsfw: bool = False) -> None:
    content_type = "nsfw" if nsfw else "sfw"
    category = random.choice(ANIME_TAGS[content_type])

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f'https://api.waifu.pics/{content_type}/{category}')

            if response.status_code == 200:
                data = response.json()
                image_url = data.get('url')
                if image_url:
                    await message.answer_photo(photo=image_url)
                else:
                    await message.answer("Zzz 😴😴😴")
            else:
                await message.answer("Zzz 😴😴😴")
        except Exception as e:
            logger.error(f"Error fetching anime image: {e}", exc_info=True)
            await message.answer("Zzz 😴😴😴")
