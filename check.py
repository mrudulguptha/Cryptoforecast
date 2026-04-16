import os
import numpy as np
import pandas as pd
import joblib
import requests

from tensorflow.keras.models import load_model
from transformers import pipeline

# ===============================
# CONFIG
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TIME_STEPS = 60

# 🔥 YOUR 10 COINS
AVAILABLE_COINS = [
    "BTC-INR", "ETH-INR", "BNB-INR", "SOL-INR",
    "DOT-INR", "XRP-INR", "TRX-INR", "DOGE-INR",
    "ADA-INR", "MATIC-INR"
]

API_KEY = "2692cdf2fd73973bba3240f03640a2b6a0dce48a"

# ===============================
# FINBERT (LAZY LOAD)
# ===============================
_finbert = None

def get_finbert():
    global _finbert
    if _finbert is None:
        print("🔄 Loading FinBERT...")
        _finbert = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert"
        )
    return _finbert


# ===============================
# INDICATORS
# ===============================
def add_indicators(df):
    df["EMA"] = df["CLOSE"].ewm(span=14).mean()
    df["RETURNS"] = df["CLOSE"].pct_change()

    delta = df["CLOSE"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    loss = loss.replace(0, 1e-10)

    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


# ===============================
# DATA PREP
# ===============================
def prepare_dataframe(path):
    df = pd.read_csv(path)
    df.columns = [c.upper() for c in df.columns]

    df["DATETIME"] = pd.to_datetime(df["DATE"] + " " + df["TIME"])
    df = df.sort_values("DATETIME").drop_duplicates("DATETIME")

    df = add_indicators(df).dropna()

    return df


# ===============================
# LOAD MODEL
# ===============================
def load_model_and_scaler(coin, mode):
    model_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_model.h5")
    scaler_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_scaler.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found for {coin} ({mode})")

    model = load_model(model_path, compile=False)
    scaler = joblib.load(scaler_path)

    return model, scaler


# ===============================
# SENTIMENT
# ===============================
def get_news_sentiment(api_key, coin):
    url = "https://cryptopanic.com/api/developer/v2/posts/"

    try:
        res = requests.get(url, params={
            "auth_token": api_key,
            "currencies": coin,
            "public": "true"
        }, timeout=10)

        if res.status_code != 200:
            return 0

        data = res.json()
        finbert = get_finbert()

        scores = []

        for post in data.get("results", [])[:10]:
            title = post.get("title", "")
            if not title:
                continue

            result = finbert(title)[0]

            if result["label"] == "positive":
                scores.append(result["score"])
            elif result["label"] == "negative":
                scores.append(-result["score"])
            else:
                scores.append(0)

        return sum(scores) / len(scores) if scores else 0

    except:
        return 0


def apply_sentiment(preds, score):
    factor = score * 0.05  # max ±5%
    return [[v * (1 + factor) for v in p] for p in preds]


# ===============================
# PREDICTION
# ===============================
def predict_future(coin, mode, steps):
    data_path = os.path.join(DATA_DIR, mode, f"{coin}_{mode}.csv")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data not found for {coin} ({mode})")

    model, scaler = load_model_and_scaler(coin, mode)
    df = prepare_dataframe(data_path)

    feature_cols = ["OPEN", "HIGH", "LOW", "CLOSE", "EMA", "RSI", "RETURNS"]

    data = df[feature_cols].values
    scaled = scaler.transform(data)

    X = scaled.copy()
    preds = []

    for _ in range(steps):
        X_input = X[-TIME_STEPS:].reshape(1, TIME_STEPS, 7)

        pred_scaled = model.predict(X_input, verbose=0)

        temp = np.zeros((1, 7))
        temp[0, :4] = pred_scaled[0]

        real = scaler.inverse_transform(temp)[0]
        preds.append(real[:4])

        new_row = np.zeros(7)
        new_row[:4] = pred_scaled[0]
        X = np.vstack([X, new_row])

    return preds


# ===============================
# MAIN API FUNCTION
# ===============================
def run_prediction(coin, mode, steps):

    if coin not in AVAILABLE_COINS:
        raise ValueError(f"Unsupported coin: {coin}")

    preds = predict_future(coin, mode, steps)

    coin_symbol = coin.split("-")[0]
    sentiment = get_news_sentiment(API_KEY, coin_symbol)

    preds = apply_sentiment(preds, sentiment)

    final = preds[-1]

    return {
        "coin": coin,
        "mode": mode,
        "sentiment": float(sentiment),
        "open": float(final[0]),
        "high": float(final[1]),
        "low": float(final[2]),
        "close": float(final[3])
    }