import re


# Список матерных и грубых слов (корни слов для более широкого покрытия)
PROFANITY_PATTERNS = [
    r'\bхуй',
    r'\bхуе',
    r'\bхуя',
    r'\bхули',
    r'\bхуев',
    r'\bпизд',
    r'\bпизж',
    r'\bебал',
    r'\bебан',
    r'\bебат',
    r'\bеби',
    r'\bъеб',
    r'\bзаеб',
    r'\bдоеб',
    r'\bпроеб',
    r'\bнаеб',
    r'\bуеб',
    r'\bвъеб',
    r'\bвыеб',
    r'\bсъеб',
    r'\bотъеб',
    r'\bразъеб',
    r'\bбля',
    r'\bблят',
    r'\bблядь',
    r'\bблядск',
    r'\bблядин',
    r'\bсука',
    r'\bсуки',
    r'\bсучк',
    r'\bсучар',
    r'\bдебил',
    r'\bдебильн',
    r'\bдолбоеб',
    r'\bдолбоящ',
    r'\bмудак',
    r'\bмудил',
    r'\bмудозвон',
    r'\bпидор',
    r'\bпидар',
    r'\bпидр',
    r'\bгандон',
    r'\bговн',
    r'\bсрать',
    r'\bсрал',
    r'\bсру',
    r'\bсрет',
    r'\bдерьм',
    r'\bдрочи',
    r'\bдроч',
    r'\bманд',
    r'\bчмо\b',
    r'\bчмош',
    r'\bдаун',
    r'\bдауни',
    r'\bретард',
    r'\bретардн',
    r'\bдаунята',
    r'\bебись',
    r'\bахуе',
    r'\bохуе',
    r'\bнахуй',
    r'\bнахер',
    r'\bпошел',
    r'\bпошл',
    r'\bидиот',
    r'\bтупиц',
    r'\bтупой',
    r'\bуебан',
    r'\bуебк',
    r'\bуебищ',
    r'\bзалуп',
    r'\bмразь',
    r'\bмрази',
    r'\bпараш',
    r'\bдаунизм',
]


def count_profanity(text: str) -> int:
    if not text:
        return 0

    text_lower = text.lower()
    count = 0

    for pattern in PROFANITY_PATTERNS:
        matches = re.findall(pattern, text_lower)
        count += len(matches)

    return count


def get_toxicity_title(count: int) -> str:
    if count == 0:
        return "😇 Ангел"
    elif count <= 5:
        return "😊 Воспитанный"
    elif count <= 20:
        return "😏 Бывает"
    elif count <= 50:
        return "🤬 Токсик"
    elif count <= 100:
        return "☠️ Матершинник"
    elif count <= 200:
        return "💀 Пиздец просто"
    else:
        return "🔥 Легенда мата"
