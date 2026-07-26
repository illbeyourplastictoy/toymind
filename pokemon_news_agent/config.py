"""Конфигурация агента новостей рынка покемонов.

Все секреты и настройки читаются из переменных окружения.
Списки лент и описание стиля — из соседних файлов feeds.txt / style.md.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Telegram ---
# Токен бота от @BotFather
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
# Куда присылать черновик на апрув (обычно твой личный chat_id).
TG_OWNER_CHAT_ID = os.getenv("TG_OWNER_CHAT_ID")
# Куда публиковать после апрува (@username канала или числовой id).
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")

# --- Claude API ---
# Ключ читается SDK автоматически из ANTHROPIC_API_KEY.
MODEL = os.getenv("POKENEWS_MODEL", "claude-opus-5")

# --- Генерация картинок (опционально, подключаемо) ---
# OpenAI-совместимый эндпоинт images/generations. Если не задан — используем
# картинку из статьи, а если и её нет — постим без картинки.
IMAGE_API_URL = os.getenv("IMAGE_API_URL")          # напр. https://api.openai.com/v1/images/generations
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")

# --- Расписание ---
CHECK_INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "6"))
# Брать новости не старше этого числа часов (окно чуть шире интервала).
NEWS_WINDOW_HOURS = float(os.getenv("NEWS_WINDOW_HOURS", "24"))
# Сколько новостей максимум учитывать в одной сводке.
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "12"))

# --- Файлы ---
FEEDS_FILE = os.path.join(BASE_DIR, "feeds.txt")
STYLE_FILE = os.path.join(BASE_DIR, "style.md")
STATE_FILE = os.getenv("POKENEWS_STATE_FILE", os.path.join(BASE_DIR, "state.json"))


def load_feeds():
    """Читает feeds.txt: по одной RSS-ссылке на строку, # — комментарий."""
    feeds = []
    try:
        with open(FEEDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    feeds.append(line)
    except FileNotFoundError:
        pass
    return feeds


def load_style():
    """Читает style.md — описание твоего стиля / примеры постов."""
    try:
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def check_required():
    """Возвращает список отсутствующих обязательных настроек."""
    missing = []
    if not TG_BOT_TOKEN:
        missing.append("TG_BOT_TOKEN")
    if not TG_OWNER_CHAT_ID:
        missing.append("TG_OWNER_CHAT_ID")
    if not TG_CHANNEL_ID:
        missing.append("TG_CHANNEL_ID")
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    return missing
