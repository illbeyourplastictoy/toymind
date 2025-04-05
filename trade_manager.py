import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

BASE_URL = "https://api.bybit.com"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")


def generate_signature(params: dict, secret: str) -> str:
    sorted_params = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(bytes(secret, "utf-8"), bytes(sorted_params, "utf-8"), hashlib.sha256).hexdigest()


def get_price(symbol: str) -> float:
    url = f"{BASE_URL}/v5/market/tickers?category=linear&symbol={symbol}"
    try:
        resp = requests.get(url)
        return float(resp.json()["result"]["list"][0]["lastPrice"])
    except:
        return 0.0


def log_trade(trade_data: dict):
    try:
        log_path = "trades_log.json"
        if not os.path.exists(log_path):
            with open(log_path, "w") as f:
                json.dump([], f)

        with open(log_path, "r") as f:
            logs = json.load(f)

        logs.append(trade_data)

        with open(log_path, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Ошибка записи лога: {e}")


def place_order(symbol: str, side: str = "Buy", order_type: str = "Market", usd_amount: float = 100):
    price = get_price(symbol)
    if price == 0:
        print(f"❌ Не удалось получить цену для {symbol}")
        return

    qty = round(usd_amount / price, 4)
    tp_price = round(price * 1.03, 4)  # TP +3%
    sl_price = round(price * 0.98, 4)  # SL -2%

    endpoint = "/v5/order/create"
    url = BASE_URL + endpoint
    timestamp = str(int(time.time() * 1000))

    params = {
        "apiKey": API_KEY,
        "timestamp": timestamp,
        "recvWindow": "5000",
        "category": "linear",
        "symbol": symbol,
        "side": side,
        "orderType": order_type,
        "qty": qty,
        "timeInForce": "GoodTillCancel",
        "takeProfit": tp_price,
        "stopLoss": sl_price,
        "reduceOnly": False,
    }

    signature = generate_signature(params, API_SECRET)
    headers = {"X-BYBIT-SIGN": signature}

    try:
        response = requests.post(url, headers=headers, json=params)
        res_json = response.json()
        print("🟢 Ордер отправлен:", res_json)

        if res_json.get("retCode") == 0:
            log_trade({
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "entry_price": price,
                "tp": tp_price,
                "sl": sl_price,
                "timestamp": datetime.utcnow().isoformat()
            })

        return res_json
    except Exception as e:
        print("❌ Ошибка при отправке ордера:", e)
        return None
