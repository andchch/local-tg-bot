# TopBot - Telegram Group Conversation Summarizer

Telegram бот для автоматического сохранения сообщений из групповых чатов и генерации AI-резюме разговоров.

## Возможности

- Автоматическое сохранение всех сообщений из группового чата
- **Распознавание голосовых сообщений и видео-кружков** с помощью Yandex SpeechKit
- Генерация кратких резюме разговоров с помощью AI (OpenAI или Anthropic)
- Поддержка временных периодов от 1 часа до 7 дней
- Простое развертывание через Docker
- Персистентное хранение данных в SQLite
- Автоматическая очистка старых сообщений

## Технологический стек

- **Python 3.11+** - основной язык
- **aiogram 3** - асинхронная библиотека для Telegram Bot API
- **SQLite** - локальная база данных
- **Yandex SpeechKit** - распознавание речи из аудио и видео
- **OpenAI / Anthropic** - AI модели для генерации резюме
- **Docker** - контейнеризация для легкого развертывания
- **FFmpeg** - обработка аудио и видео форматов

## Быстрый старт

### 1. Создание бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и выберите имя для бота
4. Сохраните полученный **токен бота** (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Отключите режим приватности командой `/setprivacy` → выберите вашего бота → `Disable`
   - Это необходимо, чтобы бот мог читать все сообщения в группе

### 2. Получение API ключей

**Yandex SpeechKit (для распознавания голосовых сообщений)**
1. Зарегистрируйтесь в [Yandex Cloud](https://cloud.yandex.ru)
2. Создайте каталог (Folder) в консоли
3. Перейдите в раздел [API Keys](https://cloud.yandex.ru/docs/iam/operations/api-key/create)
4. Создайте API ключ для сервиса SpeechKit
5. Сохраните полученный ключ

**AI для генерации резюме (выберите один вариант):**

**Вариант A: OpenAI (рекомендуется для начала)**
1. Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com)
2. Перейдите в [API Keys](https://platform.openai.com/api-keys)
3. Создайте новый ключ и сохраните его

**Вариант B: Anthropic**
1. Зарегистрируйтесь на [console.anthropic.com](https://console.anthropic.com)
2. Перейдите в раздел API Keys
3. Создайте новый ключ и сохраните его

### 3. Настройка проекта

1. Клонируйте репозиторий (или создайте файлы вручную):
```bash
git clone <repository-url>
cd topbot
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Откройте `.env` и заполните необходимые поля:
```env
# Токен вашего бота
BOT_TOKEN=ваш_токен_от_BotFather

# Yandex SpeechKit для распознавания речи
YANDEX_SPEECHKIT_API_KEY=ваш_yandex_speechkit_ключ
SPEECHKIT_MODEL=general
SPEECHKIT_LANGUAGE=ru-RU

# Выберите провайдера: "openai" или "anthropic"
AI_PROVIDER=openai

# API ключ для выбранного провайдера
OPENAI_API_KEY=ваш_openai_ключ
# или
ANTHROPIC_API_KEY=ваш_anthropic_ключ
```

### 4. Запуск с Docker (рекомендуется)

1. Убедитесь, что Docker и Docker Compose установлены:
```bash
docker --version
docker-compose --version
```

2. Соберите и запустите контейнер:
```bash
docker-compose up -d
```

3. Проверьте логи:
```bash
docker-compose logs -f bot
```

4. Остановка бота:
```bash
docker-compose down
```

### 5. Запуск без Docker (для разработки)

1. Установите Python 3.11+:
```bash
python --version  # Должна быть версия 3.11 или выше
```

2. Установите FFmpeg (требуется для распознавания речи):

**Windows:**
```bash
# Используя Chocolatey
choco install ffmpeg

# Или скачайте с https://ffmpeg.org/download.html
# и добавьте в PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

Проверьте установку:
```bash
ffmpeg -version
```

3. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Запустите бота:
```bash
python bot/main.py
```

### 6. Добавление бота в группу

1. Создайте группу в Telegram или используйте существующую
2. Добавьте бота в группу (как обычного участника)
3. Дайте боту права администратора (или убедитесь, что он может читать сообщения)
4. Отправьте команду `/start` в группе для проверки

## Команды бота

| Команда | Описание | Пример |
|---------|----------|--------|
| `/start` | Показать приветственное сообщение и инструкции | `/start` |
| `/summary [часы]` | Создать резюме разговора за последние N часов | `/summary` (24ч)<br>`/summary 12`<br>`/summary 48` |
| `/stats` | Показать статистику по сообщениям в чате | `/stats` |

## Структура проекта

```
topbot/
├── bot/
│   ├── main.py          # Точка входа, инициализация бота
│   ├── config.py        # Загрузка конфигурации из .env
│   ├── database.py      # Работа с SQLite базой данных
│   ├── handlers.py      # Обработчики команд и сообщений
│   └── summarizer.py    # Интеграция с AI для генерации резюме
├── data/                # Папка для SQLite базы данных (создается автоматически)
├── requirements.txt     # Python зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose конфигурация
├── .env                # Переменные окружения (создайте из .env.example)
├── .env.example        # Пример переменных окружения
└── README.md           # Эта инструкция
```

## Конфигурация

### Основные параметры (.env)

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | **Обязательно** |
| `YANDEX_SPEECHKIT_API_KEY` | API ключ Yandex SpeechKit | **Обязательно** |
| `SPEECHKIT_MODEL` | Модель распознавания SpeechKit | `general` |
| `SPEECHKIT_LANGUAGE` | Язык распознавания | `ru-RU` |
| `AI_PROVIDER` | Провайдер AI (`openai` или `anthropic`) | `openai` |
| `OPENAI_API_KEY` | API ключ OpenAI | **Обязательно для OpenAI** |
| `ANTHROPIC_API_KEY` | API ключ Anthropic | **Обязательно для Anthropic** |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o-mini` |
| `ANTHROPIC_MODEL` | Модель Anthropic | `claude-3-5-sonnet-20241022` |
| `DEFAULT_SUMMARY_HOURS` | Часы по умолчанию для `/summary` | `24` |
| `MAX_SUMMARY_HOURS` | Максимальное количество часов | `168` (7 дней) |
| `MESSAGE_CLEANUP_DAYS` | Хранить сообщения N дней | `30` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### Выбор AI модели

**OpenAI модели (быстрые и дешевые):**
- `gpt-4o-mini` - самая быстрая и дешевая (рекомендуется)
- `gpt-4o` - более качественные резюме, но дороже

**Anthropic модели (высокое качество):**
- `claude-3-5-sonnet-20241022` - отличный баланс скорости и качества
- `claude-3-5-haiku-20241022` - быстрая и экономичная версия

## Управление и мониторинг

### Просмотр логов
```bash
# Docker
docker-compose logs -f bot

# Без Docker (если запущено в фоне)
tail -f bot.log
```

### Рестарт бота
```bash
docker-compose restart bot
```

### Обновление бота
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Резервное копирование данных
```bash
# База данных находится в папке data/
cp data/messages.db data/messages.db.backup
```

## Решение проблем

### Бот не отвечает в группе
1. Убедитесь, что privacy mode отключен в @BotFather (`/setprivacy` → Disable)
2. Проверьте, что бот имеет права на чтение сообщений в группе
3. Проверьте логи: `docker-compose logs -f bot`

### Ошибка "BOT_TOKEN is not set"
1. Убедитесь, что файл `.env` существует
2. Проверьте, что `BOT_TOKEN` заполнен корректно
3. При использовании Docker: перезапустите контейнер

### Ошибка "Couldn't find ffprobe or avprobe"
Это означает, что FFmpeg не установлен или не найден в PATH:

**Windows:**
1. Установите FFmpeg через Chocolatey: `choco install ffmpeg`
2. Или скачайте с [ffmpeg.org](https://ffmpeg.org/download.html) и добавьте в PATH
3. Перезапустите терминал после установки

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Docker:** FFmpeg должен быть включен в Dockerfile (см. ниже)

### Ошибка при распознавании голосовых сообщений
1. Убедитесь, что `YANDEX_SPEECHKIT_API_KEY` заполнен корректно
2. Проверьте, что FFmpeg установлен (см. выше)
3. Убедитесь, что на аккаунте Yandex Cloud есть средства
4. Проверьте логи для деталей ошибки

### Ошибка при генерации резюме
1. Проверьте, что API ключ для AI провайдера валиден
2. Убедитесь, что на аккаунте есть средства (для OpenAI/Anthropic)
3. Проверьте логи для деталей ошибки

### База данных заблокирована
SQLite не поддерживает одновременный доступ. Убедитесь, что запущен только один экземпляр бота.

## Стоимость использования

### OpenAI (gpt-4o-mini)
- Ввод: ~$0.15 за 1М токенов
- Вывод: ~$0.60 за 1М токенов
- **Примерная стоимость**: $0.01-0.05 за резюме (в зависимости от объема)

### Anthropic (Claude 3.5 Sonnet)
- Ввод: ~$3 за 1М токенов
- Вывод: ~$15 за 1М токенов
- **Примерная стоимость**: $0.05-0.20 за резюме

> Для личного использования рекомендуется начать с `gpt-4o-mini` от OpenAI.

## Безопасность

- Никогда не коммитьте файл `.env` в Git
- Регулярно ротируйте API ключи
- Ограничьте доступ к серверу с ботом
- Используйте группы только с доверенными людьми
- База данных хранится локально и не передается третьим лицам

## Лицензия

MIT License - используйте свободно для личных и коммерческих целей.

## Поддержка

При возникновении проблем:
1. Проверьте раздел "Решение проблем" выше
2. Изучите логи бота
3. Создайте Issue в репозитории проекта
