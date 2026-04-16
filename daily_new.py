import requests
import datetime
import time
import csv
import os

# =============================
# CONFIG
# =============================
COINDESK_API_KEY = os.environ.get(
    "COINDESK_API_KEY",
    "5e027ecaf92277e4b9823c40ebe5f494f9c8e1d9d3e090151096d44ff40ab519"  # fallback
)

BASE_URL = "https://data-api.coindesk.com/index/cc/v1/historical/days"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_DIR = os.path.join(BASE_DIR, "data", "daily")

# Ensure directory exists
os.makedirs(DAILY_DIR, exist_ok=True)

# 3 YEARS RANGE
END_DATE = datetime.datetime.utcnow()
START_DATE = END_DATE - datetime.timedelta(days=3 * 365)


# =============================
# USD → INR
# =============================
def get_usd_to_inr():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        res = requests.get(url, timeout=10).json()
        return res["rates"]["INR"]
    except Exception as e:
        print(f"⚠ Exchange rate fetch failed: {e}. Using fallback rate 83")
        return 83


USD_TO_INR = get_usd_to_inr()
print(f"USD → INR rate: {USD_TO_INR}")


# =============================
# FETCH DATA
# =============================
def fetch_data(instrument, to_ts):
    """Fetch historical daily data from CoinDesk"""
    params = {
        "market": "cadli",
        "instrument": instrument,
        "limit": 2000,
        "aggregate": 1,
        "fill": "true",
        "apply_mapping": "true",
        "response_format": "JSON",
        "api_key": COINDESK_API_KEY,
        "to_ts": int(to_ts.timestamp())
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {instrument}: {e}")
        return {"Data": []}


# =============================
# COLLECT DATA (BACKWARD)
# =============================
def get_all_daily_data(instrument):
    """Collect 3 years of daily data"""
    all_data = []
    current_end = END_DATE

    while current_end > START_DATE:
        print(f"[{instrument}] Fetching up to {current_end.date()}")

        data = fetch_data(instrument, current_end)

        if "Data" not in data or not data["Data"]:
            print("No more data")
            break

        chunk = data["Data"]
        all_data.extend(chunk)

        # Move backward
        oldest_ts = min(row["TIMESTAMP"] for row in chunk)
        current_end = datetime.datetime.utcfromtimestamp(oldest_ts) - datetime.timedelta(days=1)

        time.sleep(1)

    return all_data


# =============================
# CLEAN + CONVERT
# =============================
def clean_data(data):
    """Clean and convert USD prices to INR"""
    cleaned = []

    for row in data:
        ts = row.get("TIMESTAMP")
        if not ts:
            continue

        dt = datetime.datetime.utcfromtimestamp(ts)

        try:
            cleaned.append({
                "DATE": dt.strftime("%Y-%m-%d"),
                "TIME": dt.strftime("%H:%M:%S"),
                "OPEN": float(row["OPEN"]) * USD_TO_INR,
                "HIGH": float(row["HIGH"]) * USD_TO_INR,
                "LOW": float(row["LOW"]) * USD_TO_INR,
                "CLOSE": float(row["CLOSE"]) * USD_TO_INR,
            })
        except (ValueError, KeyError) as e:
            print(f"Error processing row: {e}")
            continue

    return cleaned


# =============================
# SAVE
# =============================
def save_csv(data, filename):
    """Save data to CSV file"""
    if not data:
        print(f"No data to save for {filename}")
        return

    filepath = os.path.join(DAILY_DIR, filename)
    
    try:
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE"])
            writer.writeheader()
            writer.writerows(data)
        print(f"✅ Saved {len(data)} records to {filename}")
    except IOError as e:
        print(f"❌ Error saving file: {e}")


# =============================
# DOWNLOAD ALL COINS
# =============================
COINS = [
    "BTC", "ETH", "BNB", "SOL",
    "DOT", "XRP", "TRX", "DOGE",
    "ADA", "MATIC"
]

if __name__ == "__main__":
    print(f"\n📥 Downloading {len(COINS)} cryptocurrencies (daily data)...\n")

    for coin in COINS:
        print(f"\n🔄 Processing {coin}...")
        data = get_all_daily_data(coin)
        cleaned = clean_data(data)
        save_csv(cleaned, f"{coin}-INR_daily.csv")

    print("\n✅ All daily data downloaded successfully!")
