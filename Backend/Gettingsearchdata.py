from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)  # 🔥 This line allows frontend to access backend

@app.route('/')
def home():
    return "Flask server is running!"

@app.route('/stock/<symbol>')
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)  # Already includes ".NS" in your frontend
        price = stock.info['regularMarketPrice']
        return jsonify({"symbol": symbol.upper(), "price": price})
    except Exception as e:
        return jsonify({"error": "Failed to fetch price", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
