from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import render_template
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, time
from pymongo import MongoClient
import bcrypt
import re
from bson import ObjectId

app = Flask(__name__)
CORS(app)

# 🔹 MongoDB connect
client = MongoClient("mongodb+srv://harshitgupta241005_db_user:k9DjQ1ho4gJEclbL@cluster0.z7evgik.mongodb.net/")
db = client["bullspire"]
collection = db["users"]
portfolio = db["portfolio"] 


# 🔥 unique gmail
collection.create_index("gmail", unique=True)

# 🔹 email validation
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# =========================
# HOME
# =========================
@app.route('/')
def home():
    return "MongoDB server running 🚀"


# =========================
# REGISTER
# =========================
@app.route('/save_user', methods=['POST'])
def save_user():
    try:
        data = request.get_json()

        username = data.get('username')
        gmail = data.get('gmail')
        password = data.get('password')

        if not username or not gmail or not password:
            return jsonify({"message": "Missing fields"}), 400

        if not is_valid_email(gmail):
            return jsonify({"message": "Invalid email"}), 400

        # 🔐 hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # 💾 save
        collection.insert_one({
            "username": username,
            "gmail": gmail,
            "password": hashed,
            "balance": 1000000
        })

        return jsonify({
            "message": "Registration successful",
            "user_id": str(result.inserted_id)   # ⭐ MOST IMPORTANT
        }), 201

    except Exception as e:
        # duplicate handle
        if "duplicate key error" in str(e).lower():
            return jsonify({"message": "Email already registered"}), 409
        
        return jsonify({"message": "Server error", "error": str(e)}), 500


# =========================
# LOGIN
# =========================

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        gmail = data.get('gmail')
        password = data.get('password')

        if not gmail or not password:
            return jsonify({"message": "Missing credentials"}), 400

        user = collection.find_one({"gmail": gmail})

        if not user:
            return jsonify({"message": "User not found"}), 404

        # 🔐 check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({
                "message": "Login successful",
                "username": user['username'],
                "gmail": user['gmail'],
                "user_id": str(user['_id'])
            }), 200
        else:
            return jsonify({"message": "Wrong password"}), 401

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


# =========================
# RUN
# =========================
#if __name__ == '__main__':
    #app.run(debug=True)
# ✅ Render stock page
@app.route('/stock/<symbol>')
def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # 🔥 1. Fast & reliable data (works even when market closed)
        fast = ticker.fast_info

        price = fast.get("last_price", None)
        prev = fast.get("previous_close", None)

        # 🔥 fallback if fast_info fails
        if not price or not prev:
            hist = ticker.history(period="2d")

            if not hist.empty:
                price = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
            else:
                price = prev = 0

        change = round(price - prev, 2)
        percent = round((change / prev) * 100, 2) if prev else 0

        # 🔥 safe info fetch (optional fields)
        info = {}
        try:
            info = ticker.info
        except:
            pass

        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('longName', symbol.upper()),
            "price": round(price, 2),
            "change": change,
            "percent": percent,
            "marketCap": info.get('marketCap', 'N/A'),
            "peRatio": info.get('trailingPE', 'N/A'),
            "weekHigh": info.get('fiftyTwoWeekHigh', 'N/A'),
            "weekLow": info.get('fiftyTwoWeekLow', 'N/A'),
            "volume": info.get('volume', 'N/A'),
            "avgVolume": info.get('averageVolume', 'N/A')
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "symbol": symbol.upper(),
            "name": symbol.upper(),
            "price": 0,
            "change": 0,
            "percent": 0,
            "error": "Data unavailable (market closed or API issue)"
        })

# Live indices and stocks
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



    if __name__ == '__main__':
      app.run(debug=True)
# @app.route('/candles/<symbol>')
# def get_candles(symbol):
#     try:
#         ticker = yf.Ticker(symbol)
#         data = ticker.history(period="1d", interval="5m", auto_adjust=False)
        
#         if data.empty:
#             return jsonify({"error": "No data found"}), 404
            
#         candles = []
#         for index, row in data.iterrows():
#             if not any(pd.isna([row['Open'], row['High'], row['Low'], row['Close']])):  # ignore NaN rows
#                 candles.append({
#                     "x": index.isoformat(),
#                     "o": round(row['Open'], 2),
#                     "h": round(row['High'], 2),
#                     "l": round(row['Low'], 2),
#                     "c": round(row['Close'], 2)
#                 })
        
#         return jsonify(candles)
        
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# import yfinance as yf
import json
# from flask import jsonify

@app.route('/api/top_stocks')
def top_stocks():

    with open("stocks.json", "r") as f:
        stocks = json.load(f)

    symbols = [s["symbol"] + ".NS" for s in stocks]

    stocks_data = []

    data = yf.download(symbols, period="2d")["Close"]

    # ❗ check data valid hai ya nahi
    if data is None or len(data) < 2:
        return jsonify({"gainers": [], "losers": []})

    for stock in stocks:
        sym = stock["symbol"] + ".NS"

        try:
            # ❗ safe check
            if sym not in data.columns:
                print("Missing:", sym)
                continue

            prev = data[sym].iloc[-2]
            last = data[sym].iloc[-1]

            change = last - prev
            percent = (change / prev) * 100

            stocks_data.append({
                "name": stock["name"],
                "symbol": sym,
                "price": round(float(last), 2),
                "change": round(float(change), 2),
                "percent": round(float(percent), 2)
            })

        except Exception as e:
            print("Error:", sym, e)
            continue

    # ❗ agar empty hai to check kar
    print("TOTAL STOCKS:", len(stocks_data))

    gainers = sorted(stocks_data, key=lambda x: x["percent"], reverse=True)
    losers = sorted(stocks_data, key=lambda x: x["percent"])

    return jsonify({
        "gainers": gainers[:10],
        "losers": losers[:10]
    })
    import yfinance as yf

data = yf.download("RELIANCE.NS", period="2d")
#print(data)
# ================== BUY STOCK ==================
# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from datetime import datetime
# import yfinance as yf
# from flask_cors import CORS
# import os

# app = Flask(__name__)
# CORS(app)

# MongoDB
# MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://harshitgupta241005_db_user:k9DjQ1ho4gJEclbL@cluster0.z7evgik.mongodb.net/"

# client = MongoClient(MONGO_URI)
# db = client["bullspire"]
# portfolio = db["portfolio"]

# 🔥 symbol fix
# def format_symbol(symbol):
#     symbol = symbol.upper()
#     if symbol.endswith(".NS") or symbol.startswith("^"):
#         return symbol
#     return symbol + ".NS"

# ================== BUY ==================
# @app.route('/buy', methods=['POST'])
# def buy_stock():
#     data = request.json
#     print("DATA RECEIVED:", data)  # debug

    # user_id = data.get("user_id")
    # symbol = format_symbol(data.get("symbol"))
    # qty = int(data.get("quantity", 1))
    # price = float(data.get("price", 0))

    # if not user_id:
    #     return jsonify({"error": "user_id missing"}), 400

    # total = qty * price

    # existing = portfolio.find_one({
    #     "user_id": user_id,
    #     "symbol": symbol
    # })

    # if existing:
    #     new_qty = existing["quantity"] + qty
    #     new_total = existing["total_investment"] + total
    #     new_avg = new_total / new_qty

    #     portfolio.update_one(
    #         {"_id": existing["_id"]},
    #         {"$set": {
    #             "quantity": new_qty,
    #             "avg_price": new_avg,
    #             "total_investment": new_total
    #         }}
    #     )
    # else:
    #     portfolio.insert_one({
    #         "user_id": user_id,
    #         "symbol": symbol,
    #         "quantity": qty,
    #         "avg_price": price,
    #         "total_investment": total,
    #         "created_at": datetime.now()
    #     })

    # return jsonify({"message": "Stock Bought 🚀"})


# ================== PORTFOLIO ==================
# @app.route('/portfolio/<user_id>')
# def get_portfolio(user_id):

#     stocks = list(portfolio.find({"user_id": user_id}))

#     result = []
#     total_invested = 0
#     total_profit = 0

#     for stock in stocks:
#         symbol = stock["symbol"]
#         ticker = yf.Ticker(symbol)

#         try:
#             price = ticker.fast_info.get("last_price", 0)
#         except:
#             price = 0

#         qty = stock["quantity"]
#         avg = stock["avg_price"]

#         investment = stock["total_investment"]
#         profit = (price - avg) * qty

#         total_invested += investment
#         total_profit += profit

#         result.append({
#             "symbol": symbol,
#             "quantity": qty,
#             "avg_price": avg,
#             "current_price": round(price, 2),
#             "profit": round(profit, 2)
#         })

#     return jsonify({
#         "stocks": result,
#         "total_invested": round(total_invested, 2),
#         "total_profit": round(total_profit, 2)
#     })

def format_symbol(symbol):
    symbol = symbol.upper()
    if symbol.endswith(".NS") or symbol.startswith("^"):
        return symbol
    return symbol + ".NS"


@app.route('/buy', methods=['POST', 'OPTIONS'])
def buy_stock():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        data = request.json
        
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id missing"}), 400

        # 🔥 STRING → OBJECTID (ONLY ONCE)
        user_obj_id = ObjectId(user_id)

        user = collection.find_one({"_id": user_obj_id})
        if not user:
            return jsonify({"error": "User not found"}), 401

        symbol = format_symbol(data.get("symbol")).upper()
        qty = int(data.get("quantity", 1))
        price = float(data.get("price", 0))
        total = qty * price

         # 💰 CHECK BALANCE
        balance = user.get("balance", 0)

        if balance < total:
            
            return jsonify({"error": "Insufficient balance"}), 400

        # 🔥 DEDUCT BALANCE
        collection.update_one(
            {"_id": user_obj_id},
            {"$inc": {"balance": -total}}
        )

        # 🔄 Portfolio update
        existing = portfolio.find_one({
            "user_id": user_obj_id,
            "symbol": symbol
        })

        if existing:
            new_qty = existing["quantity"] + qty
            new_total = existing["total_investment"] + total
            new_avg = new_total / new_qty

            portfolio.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "quantity": new_qty,
                    "avg_price": new_avg,
                    "total_investment": new_total
                }}
            )
        else:
            portfolio.insert_one({
                "user_id": user_obj_id,
                "username": user["username"],
                "symbol": symbol,
                "quantity": qty,
                "avg_price": price,
                "total_investment": total,
                "created_at": datetime.now()
            })

        # 🆕 Updated balance fetch
        updated_user = collection.find_one({"_id": user_obj_id})

        return jsonify({
            "success": True,
            "message": f"Bought successfully {symbol} ",
            "remaining_balance": updated_user["balance"]
        })

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500
# 🔥 Portfolio by userid


@app.route('/portfolio/<user_id>')
def get_portfolio(user_id):
    try:
        user_obj_id = ObjectId(user_id)

        stocks = list(portfolio.find({"user_id": user_obj_id}))
        
        result = []
        total_invested = 0
        total_profit = 0
        total_today_profit = 0   # 🔥 NEW
        total_value = 0

        for stock in stocks:
            symbol = stock["symbol"]
            ticker = yf.Ticker(symbol)

            # 🔥 PRICE FETCH (LIVE + FALLBACK)
            try:
                hist = ticker.history(period="2d")

                if len(hist) >= 2:
                    current_price = hist["Close"].iloc[-1]
                    prev_close = hist["Close"].iloc[-2]
                elif len(hist) == 1:
                    current_price = hist["Close"].iloc[-1]
                    prev_close = current_price
                else:
                    current_price = 0
                    prev_close = 0

            except:
                current_price = 0
                prev_close = 0

            qty = stock["quantity"]
            avg = stock["avg_price"]
            investment = stock["total_investment"]

            # 🔥 CALCULATIONS
            current_value = current_price * qty
            total_profit_stock = (current_price - avg) * qty
            buy_date = stock["created_at"].date()
            today = datetime.now().date()

            if buy_date == today:
             today_profit_stock = total_profit_stock   # 🔥 aaj buy kiya
            else:
             today_profit_stock = (current_price - prev_close) * qty

            # 🔥 TOTALS
            total_invested += investment
            total_profit += total_profit_stock
            total_today_profit += today_profit_stock
            total_value += current_value

            result.append({
                "symbol": symbol.replace('.NS',''),
                "quantity": qty,
                "avg_price": round(avg, 2),
                "current_price": round(current_price, 2),
                "prev_close": round(prev_close, 2),   # optional
                "current_value": round(current_value, 2),
                "profit": round(total_profit_stock, 2),
                "today_profit": round(today_profit_stock, 2),  # 🔥 NEW
                "invested": round(investment, 2),
                "date": str(stock["created_at"])
            })

        return jsonify({
            "stocks": result,
            "total_invested": round(total_invested, 2),
            "total_profit": round(total_profit, 2),
            "today_profit": round(total_today_profit, 2),   # 🔥 NEW
            "total_value": round(total_value, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)})
    
    # fetching balance and invested amount
@app.route('/profile/<user_id>')
def get_profile(user_id):
    try:
        user_obj_id = ObjectId(user_id)

        # 🔍 user find
        user = collection.find_one({"_id": user_obj_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 💰 balance
        balance = user.get("balance", 0)

        # 📊 invested (portfolio se sum)
        pipeline = [
            {"$match": {"user_id": user_obj_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$total_investment"}
            }}
        ]

        result = list(portfolio.aggregate(pipeline))
        invested = result[0]["total"] if result else 0

        return jsonify({
            "balance": balance,
            "invested": invested
        })

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/add_money', methods=['POST', 'OPTIONS'])
def add_money():

    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200   # 🔥 ye line important

    try:
        data = request.json

        user_id = data.get("user_id")
        amount = float(data.get("amount", 0))

        if not user_id or amount <= 0:
            return jsonify({"error": "Invalid data"}), 400

        user_obj_id = ObjectId(user_id)

        collection.update_one(
            {"_id": user_obj_id},
            {"$inc": {"balance": amount}}
        )

        user = collection.find_one({"_id": user_obj_id})

        return jsonify({
            "success": True,
            "message": "Money added 💰",
            "new_balance": user["balance"]
        })

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')




