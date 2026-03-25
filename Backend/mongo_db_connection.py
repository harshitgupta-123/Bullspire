import os
from pymongo import MongoClient
import bcrypt

# 🔐 Mongo URI (best: env variable use kar)
MONGO_URI = os.getenv("MONGO_URI")

# fallback (agar env set nahi hai)
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://harshitgupta241005_db_user:k9DjQ1ho4gJEclbL@cluster0.z7evgik.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["bullspire"]
# collection = db["users"]

print(client.list_database_names())

# # # 🔹 user data
# # username = "harshit"
# # gmail = "test@gmail.com"
# # password = "1234"

# # # 🔐 password hash
# # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# # # 💾 save in DB
# # collection.insert_one({
# #     "username": username,
# #     "gmail": gmail,
# #     "password": hashed_password
# # })

# # print("User inserted successfully ✅")
# # username = "rahul"
# # gmail = "rahul@gmail.com"
# # password = "5678"

# # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# # collection.insert_one({
# #     "username": username,
# #     "gmail": gmail,
# #     "password": hashed_password
# # })
# # print("user2 inserted successfully")
# collection=db['portfolio']
# from flask import Flask, request, jsonify
# import yfinance as yf
# from datetime import datetime
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# portfolio = db["portfolio"]   # already tera hai

# # 🔥 symbol fix
# def format_symbol(symbol):
#     symbol = symbol.upper()
#     if symbol.endswith(".NS") or symbol.startswith("^"):
#         return symbol
#     return symbol + ".NS"


# # ================== BUY API ==================
# @app.route('/buy', methods=['POST'])
# def buy_stock():
#     data = request.json

#     print("DATA RECEIVED:", data)  # 🔥 debug

#     user_id = data.get("user_id")
#     symbol = format_symbol(data.get("symbol"))
#     qty = data.get("quantity")
#     price = data.get("price")

#     if not user_id or not symbol or not price:
#         return jsonify({"error": "Missing data"}), 400

#     total = qty * price

#     existing = portfolio.find_one({
#         "user_id": user_id,
#         "symbol": symbol
#     })

#     if existing:
#         new_qty = existing["quantity"] + qty
#         new_total = existing["total_investment"] + total
#         new_avg = new_total / new_qty

#         portfolio.update_one(
#             {"_id": existing["_id"]},
#             {"$set": {
#                 "quantity": new_qty,
#                 "avg_price": new_avg,
#                 "total_investment": new_total
#             }}
#         )
#     else:
#         portfolio.insert_one({
#             "user_id": user_id,
#             "symbol": symbol,
#             "quantity": qty,
#             "avg_price": price,
#             "total_investment": total,
#             "created_at": datetime.now()
#         })

#     return jsonify({"message": "Stock Bought Successfully 🚀"})


# # ================== PORTFOLIO API ==================
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
#             "profit": round(profit, 2),
#             "created_at": stock.get("created_at")
#         })

#     return jsonify({
#         "stocks": result,
#         "total_invested": round(total_invested, 2),
#         "total_profit": round(total_profit, 2)
#     })


# # ================== RUN ==================
# if __name__ == "__main__":
#     app.run(debug=True)