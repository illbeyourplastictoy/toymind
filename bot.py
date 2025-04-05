import os
import time
from telegram_messenger import send_telegram
from logic import get_trade_opportunities
from trade_manager import place_order

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
    print("⚠️ Telegram уведомления отключены.")
else:
    send_telegram("🤖 ToyMind запущен. Мониторю рынок...", TG_TOKEN, TG_CHAT_ID)
    print("📨 Стартовое сообщение отправлено в Telegram.")

# Главный цикл
while True:
    print("🔄 ToyMind жив. Проверяю рынок...")
    opportunities = get_trade_opportunities()
    if opportunities:
        for opp in opportunities:
            symbol = opp['symbol']
            price = opp['price']
            volume = opp['volume']

            msg = f"🚀 Найдена монета: {symbol}\nЦена: {price}\nОбъём: {volume}\nОткрываю позицию на $100..."
            print(msg)
            if TG_TOKEN and TG_CHAT_ID:
                send_telegram(msg, TG_TOKEN, TG_CHAT_ID)

            # Торговля
            try:
                result = place_order(symbol=symbol, qty=0.01)  # Пример: 0.01 BTC или эквивалент
                print("📈 Ответ от Bybit:", result)
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(f"✅ Ордер отправлен: {symbol}", TG_TOKEN, TG_CHAT_ID)
            except Exception as e:
                print("❌ Ошибка при торговле:", e)
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(f"❌ Ошибка при попытке открыть ордер: {e}", TG_TOKEN, TG_CHAT_ID)
    else:
        print("😴 Нет подходящих монет сейчас.")
    time.sleep(60)
