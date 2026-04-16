import requests
import datetime
import time
import csv
import os

# =============================
# CONFIG
# =============================
API_KEY = "5e027ecaf92277e4b9823c40ebe5f494f9c8e1d9d3e090151096d44ff40ab519"

BASE_URL = "https://data-api.coindesk.com/index/cc/v1/historical/days"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_DIR = os.path.join(BASE_DIR, "data", "daily")

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
    except:
        print("⚠ Using fallback rate 83")
        return 83


USD_TO_INR = get_usd_to_inr()
print(f"USD → INR rate: {USD_TO_INR}")


# =============================
# FETCH DATA
# =============================
def fetch_data(instrument, to_ts):
    params = {
        "market": "cadli",
        "instrument": instrument,
        "limit": 2000,
        "aggregate": 1,
        "fill": "true",
        "apply_mapping": "true",
        "response_format": "JSON",
        "api_key": API_KEY,
        "to_ts": int(to_ts.timestamp())
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {instrument}: {e}")
        return {"Data": []}


# =============================
# COLLECT DATA (BACKWARD)
# =============================
def get_all_daily_data(instrument):
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
    cleaned = []

    for row in data:
        ts = row.get("TIMESTAMP")
        if not ts:
            continue

        dt = datetime.datetime.utcfromtimestamp(ts)

        if dt < START_DATE:
            continue

        open_p = (row.get("OPEN") or 0) * USD_TO_INR
        high_p = (row.get("HIGH") or 0) * USD_TO_INR
        low_p = (row.get("LOW") or 0) * USD_TO_INR
        close_p = (row.get("CLOSE") or 0) * USD_TO_INR

        cleaned.append({
            "DATE": dt.strftime("%Y-%m-%d"),
            "TIME": dt.strftime("%H:%M:%S"),
            "OPEN": round(open_p, 2),
            "HIGH": round(high_p, 2),
            "LOW": round(low_p, 2),
            "CLOSE": round(close_p, 2)
        })

    return cleaned


# =============================
# SAVE CSV
# =============================
def save_to_csv(data, instrument):
    if not data:
        print(f"No data for {instrument}")
        return

    file_path = os.path.join(DAILY_DIR, f"{instrument}_daily.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE"]
        )
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Saved {instrument} → {file_path} ({len(data)} rows)")


# =============================
# MAIN
# =============================
def main():
    instruments = [
        "BTC-USD",
        "ETH-USD",
        "BNB-USD",
        "SOL-USD",
        "DOT-USD",
        "XRP-USD",
        "TRX-USD",
        "DOGE-USD",
        "ADA-USD",
        "MATIC-USD"
    ]

    for instrument in instruments:
        print(f"\n=== Fetching DAILY data for {instrument} (3 years) ===")

        raw_data = get_all_daily_data(instrument)
        cleaned = clean_data(raw_data)

        save_to_csv(cleaned, instrument.replace("USD", "INR"))


if __name__ == "__main__":
    main()