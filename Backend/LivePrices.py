from flask import Flask, jsonify
import yfinance as yf
from flask_cors import CORS
from datetime import datetime, time

def is_market_open():
    now = datetime.now().time()
    return time(9, 15) <= now <= time(15, 30)

app = Flask(__name__)
CORS(app)

@app.route('/api/live_prices')
def get_live_data():
    data = []

    # ✅ Indices
    indices = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "MIDCAP NIFTY": "^NSEMDCP50",
    }

    # ✅ Stocks
    stocks = {
        "Hindustan Zinc": "HINDZINC.NS",
        "Reliance Power": "RPOWER.NS",
        "Tata Steel": "TATASTEEL.NS",
        "NTPC Limited": "NTPC.NS"
    }

    def get_price_data(symbol):
        try:
            ticker = yf.Ticker(symbol)

            # 🔥 1. Try fast_info (BEST & FAST)
            last = ticker.fast_info.get("last_price", None)
            prev = ticker.fast_info.get("previous_close", None)

            if last and prev:
                return round(last, 2), round(prev, 2)

            # 🔥 2. Fallback → intraday
            hist = ticker.history(period="1d", interval="1m")

            if not hist.empty:
                last = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[0]
                return round(last, 2), round(prev, 2)

            # 🔥 3. Final fallback → daily
            hist_daily = ticker.history(period="2d")

            if not hist_daily.empty:
                last = hist_daily["Close"].iloc[-1]
                prev = hist_daily["Close"].iloc[-2] if len(hist_daily) > 1 else last
                return round(last, 2), round(prev, 2)

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

        return 0, 0

    # ✅ Process Indices
    for name, symbol in indices.items():
        last, prev = get_price_data(symbol)

        change = round(last - prev, 2)
        percent = round((change / prev) * 100, 2) if prev else 0

        data.append({
            "type": "index",
            "name": name,
            "symbol": symbol,
            "price": last,
            "change": change,
            "percent": percent
        })

    # ✅ Process Stocks
    for name, symbol in stocks.items():
        last, prev = get_price_data(symbol)

        change = round(last - prev, 2)
        percent = round((change / prev) * 100, 2) if prev else 0

        data.append({
            "type": "stock",
            "name": name,
            "symbol": symbol,
            "price": last,
            "change": change,
            "percent": percent
        })

    return jsonify(data)


#if __name__ == '__main__':
    app.run(debug=True)
