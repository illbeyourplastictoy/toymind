import os
import time
from telegram_messenger import send_telegram
from logic import get_trade_opportunities
from trade_manager import place_order

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

if not API_KEY or not API_SECRET:
    print("❌ Нет API-ключей Bybit.")
else:
    print("✅ API-ключи Bybit загружены.")

if not TG_TOKEN or not TG_CHAT_ID:
    print("⚠️ Нет ключей Telegram. Уведомления отключены.")
else:
    send_telegram("🤖 ToyMind запущен. Мониторю рынок...", TG_TOKEN, TG_CHAT_ID)

used_symbols = set()

while True:
    print("🔄 Проверка рынка...")
    try:
        opportunities = get_trade_opportunities()
        for opp in opportunities:
            symbol = opp["symbol"]
            side = opp["side"]
            price = opp["price"]

            if symbol in used_symbols:
                continue

            used_symbols.add(symbol)

            msg = f"📊 Сигнал: {side} по {symbol}\nЦена: {price}\nОткрываю позицию на $100..."
            print(msg)
            if TG_TOKEN and TG_CHAT_ID:
                send_telegram(msg, TG_TOKEN, TG_CHAT_ID)

            result = place_order(symbol=symbol, side=side, usd_amount=100)

            if result:
                print("✅ Ордер отправлен.")
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(f"✅ Ордер отправлен: {symbol} {side}", TG_TOKEN, TG_CHAT_ID)
            else:
                print("❌ Ошибка при открытии сделки")
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(f"❌ Не удалось открыть сделку по {symbol}", TG_TOKEN, TG_CHAT_ID)

    except Exception as e:
        print(f"⚠️ Ошибка в основном цикле: {e}")

    time.sleep(60)
