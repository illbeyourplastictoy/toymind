import requests

# Заглушка: позже можно подключить реальный API Bybit

def get_trade_opportunities():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        response = requests.get(url)
        data = response.json()
        result = []

        for item in data.get("result", {}).get("list", []):
            symbol = item.get("symbol")
            last_price = float(item.get("lastPrice", 0))
            volume = float(item.get("turnover24h", 0))

            # Фильтр: объём торгов больше 10 миллионов
            if volume > 10_000_000:
                result.append({
                    "symbol": symbol,
                    "price": last_price,
                    "volume": volume
                })

        return result

    except Exception as e:
        print(f"Ошибка при получении тикеров: {e}")
        return []

