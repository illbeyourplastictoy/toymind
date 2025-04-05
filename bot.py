import os
import time
from telegram_messenger import send_telegram

# Читаем ключи из переменных окружения
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# Проверка на наличие всех ключей
if not API_KEY or not API_SECRET:
    print("❌ Ошибка: отсутствуют ключи от Bybit API.")
else:
    print("✅ Ключи от Bybit API загружены.")

if not TG_TOKEN or not TG_CHAT_ID:
    print("⚠️ Предупреждение: отсутствуют ключи для Telegram. Уведомления не будут отправляться.")
else:
    send_telegram("🤖 ToyMind запущен. Начинаю мониторинг рынка...", TG_TOKEN, TG_CHAT_ID)
    print("📨 Сообщение отправлено в Telegram.")

# Простейший цикл, чтобы бот не завершался
while True:
    print("🔄 ToyMind жив. Жду сигналов... (обновление каждые 60 сек)")
    time.sleep(60)
