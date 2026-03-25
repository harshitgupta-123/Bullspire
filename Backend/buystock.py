from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import yfinance as yf
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# MongoDB - 2 collections
client = MongoClient("mongodb+srv://harshitgupta241005_db_user:k9DjQ1ho4gJEclbL@cluster0.z7evgik.mongodb.net/", serverSelectionTimeoutMS=5000)
db = client["bullspire"]
users = db["users"]           # Your existing login collection
portfolio = db["portfolio"]   # Trading collection

# Keep ALL your existing functions (register, login, stock APIs)
users.create_index("gmail", unique=True)

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

def format_symbol(symbol):
    symbol = symbol.upper()
    if symbol.endswith(".NS") or symbol.startswith("^"):
        return symbol
    return symbol + ".NS"

# 🔥 YOUR /buy endpoint - MODIFIED for gmail user_id
@app.route('/buy', methods=['POST'])
def buy_stock():
    try:
        data = request.json
        print("📦 BUY DATA:", data)
        
        gmail = data.get("gmail")  # 🔥 Use gmail as user_id
        symbol = format_symbol(data.get("symbol"))
        qty = int(data.get("quantity", 1))
        price = float(data.get("price", 0))

        if not gmail:
            return jsonify({"error": "gmail missing"}), 400

        # 🔥 Verify user exists (your users collection)
        user = users.find_one({"gmail": gmail})
        if not user:
            return jsonify({"error": "User not found. Login first!"}), 401

        total = qty * price
        
        existing = portfolio.find_one({"gmail": gmail, "symbol": symbol})
        if existing:
            new_qty = existing["quantity"] + qty
            new_total = existing["total_investment"] + total
            new_avg = new_total / new_qty
            portfolio.update_one(
                {"_id": existing["_id"]},
                {"$set": {"quantity": new_qty, "avg_price": new_avg, "total_investment": new_total}}
            )
            print(f"📝 Updated {symbol} for {user['username']}")
        else:
            portfolio.insert_one({
                "gmail": gmail,           # 🔥 Link by gmail
                "username": user['username'],
                "symbol": symbol,
                "quantity": qty,
                "avg_price": price,
                "total_investment": total,
                "created_at": datetime.now()
            })
            print(f"✅ BOUGHT {symbol} for {user['username']}")

        return jsonify({"message": f"Bought {symbol} 🚀"})
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": str(e)}), 500

# 🔥 Portfolio by gmail
@app.route('/portfolio/<gmail>')
def get_portfolio(gmail):
    stocks = list(portfolio.find({"gmail": gmail}))
    
    result = []
    total_invested = 0
    total_profit = 0
    
    for stock in stocks:
        symbol = stock["symbol"]
        ticker = yf.Ticker(symbol)
        try:
            price = ticker.fast_info.get("last_price", 0)
        except:
            price = 0
            
        qty = stock["quantity"]
        avg = stock["avg_price"]
        investment = stock["total_investment"]
        profit = (price - avg) * qty
        
        total_invested += investment
        total_profit += profit
        
        result.append({
            "symbol": symbol.replace('.NS', ''),
            "quantity": qty,
            "avg_price": round(avg, 2),
            "current_price": round(price, 2),
            "profit": round(profit, 2)
        })
    
    return jsonify({
        "stocks": result,
        "total_invested": round(total_invested, 2),
        "total_profit": round(total_profit, 2)
    })

    # ... your full code ...

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

# Your portfolio endpoint stays same...
