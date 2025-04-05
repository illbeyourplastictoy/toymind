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
    send_telegram("🤖 ToyMind V1.5 запущен. Мониторю рынок с TP/SL и логированием...", TG_TOKEN, TG_CHAT_ID)

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

            msg = (
                f"📊 Сигнал: {side} по {symbol}\n"
                f"Цена: {price}\n"
                f"Открываю позицию на $100 с TP +3% и SL -2%..."
            )
            print(msg)
            if TG_TOKEN and TG_CHAT_ID:
                send_telegram(msg, TG_TOKEN, TG_CHAT_ID)

            result = place_order(symbol=symbol, side=side, usd_amount=100)

            if result and result.get("retCode") == 0:
                confirm = f"✅ Сделка открыта: {symbol} {side} @ {price} (с TP/SL)"
                print(confirm)
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(confirm, TG_TOKEN, TG_CHAT_ID)
            else:
                error = f"❌ Не удалось открыть сделку по {symbol}"
                print(error)
                if TG_TOKEN and TG_CHAT_ID:
                    send_telegram(error, TG_TOKEN, TG_CHAT_ID)

    except Exception as e:
        print(f"⚠️ Ошибка в основном цикле: {e}")

    time.sleep(60)
