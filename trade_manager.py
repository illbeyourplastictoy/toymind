import os
import time
import hmac
import hashlib
import requests

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


def place_order(symbol: str, side: str = "Buy", order_type: str = "Market", usd_amount: float = 100):
    price = get_price(symbol)
    if price == 0:
        print(f"❌ Не удалось получить цену для {symbol}")
        return

    qty = round(usd_amount / price, 4)

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
        "reduceOnly": False,
    }

    signature = generate_signature(params, API_SECRET)
    headers = {"X-BYBIT-SIGN": signature}

    try:
        response = requests.post(url, headers=headers, json=params)
        print("🟢 Ордер отправлен:", response.json())
        return response.json()
    except Exception as e:
        print("❌ Ошибка при отправке ордера:", e)
        return None
