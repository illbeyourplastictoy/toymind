import os
import requests
import time
import hmac
import hashlib

BASE_URL = "https://api.bybit.com"

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")


def generate_signature(params: dict, secret: str) -> str:
    sorted_params = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(bytes(secret, "utf-8"), bytes(sorted_params, "utf-8"), hashlib.sha256).hexdigest()


def place_order(symbol: str, side: str = "Buy", qty: float = 0.01, order_type: str = "Market"):
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
        "timeInForce": "GoodTillCancel"
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
