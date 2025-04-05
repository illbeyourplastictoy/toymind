import requests
import pandas as pd

def get_trade_opportunities():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
 response = requests.get(url)
if response.status_code != 200 or not response.text.strip():
    print(f"❌ Пустой или неверный ответ от API: {response.status_code}")
    return []

try:
    data = response.json()
except Exception as e:
    print(f"❌ Ошибка разбора JSON: {e}")
    print("Ответ:", response.text)
    return []
try:
    data = response.json()
except Exception as e:
    print(f"❌ Ошибка разбора JSON: {e}")
    print("Ответ:", response.text)
    return []

        for item in data.get("result", {}).get("list", []):
            symbol = item.get("symbol")
            if not symbol.endswith("USDT"):
                continue

            try:
                klines_url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=1&limit=25"
                klines_resp = requests.get(klines_url)
                klines_data = klines_resp.json().get("result", {}).get("list", [])

                if len(klines_data) < 21:
                    continue

                closes = [float(candle[4]) for candle in klines_data]  # close prices
                df = pd.DataFrame({"close": closes})
                df["EMA5"] = df["close"].ewm(span=5).mean()
                df["EMA21"] = df["close"].ewm(span=21).mean()

                last_close = df.iloc[-1]["close"]
                ema5 = df.iloc[-1]["EMA5"]
                ema21 = df.iloc[-1]["EMA21"]

                side = None
                if ema5 > ema21:
                    side = "Buy"
                elif ema5 < ema21:
                    side = "Sell"

                if side:
                    result.append({
                        "symbol": symbol,
                        "price": last_close,
                        "side": side
                    })
            except Exception as inner_e:
                print(f"Ошибка по {symbol}: {inner_e}")
                continue

        return result

    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return []
