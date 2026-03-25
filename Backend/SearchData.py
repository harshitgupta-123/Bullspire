import csv
import json

stocks = []

with open("EQUITY_L.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    reader.fieldnames = [field.strip() for field in reader.fieldnames]

    for row in reader:
        try:
            name = row["NAME OF COMPANY"].strip().title()
            symbol = row["SYMBOL"].strip().upper() + ".NS"
            stocks.append({"name": name, "symbol": symbol})
        except KeyError as e:
            print(f"⚠️ Missing column: {e}")
            continue

with open("stocks.json", "w", encoding="utf-8") as f:
    json.dump(stocks, f, indent=2)

print(f"✅ Converted {len(stocks)} stocks to stocks.json")
