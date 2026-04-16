import os
import sys
import numpy as np
import pandas as pd
import joblib
import requests
from tensorflow.keras.models import load_model
from transformers import pipeline

# ===============================
# CONFIG - PATHS
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TIME_STEPS = 60

# Verify directories exist
if not os.path.exists(DATA_DIR):
    raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")
if not os.path.exists(MODEL_DIR):
    raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")

# ===============================
# CONFIG - API KEYS (FROM ENV)
# ===============================
CRYPTOPANIC_API_KEY = os.environ.get(
    "CRYPTOPANIC_API_KEY",
    "2692cdf2fd73973bba3240f03640a2b6a0dce48a"  # fallback for local dev
)

# 🔥 YOUR 10 COINS
AVAILABLE_COINS = [
    "BTC-INR", "ETH-INR", "BNB-INR", "SOL-INR",
    "DOT-INR", "XRP-INR", "TRX-INR", "DOGE-INR",
    "ADA-INR", "MATIC-INR"
]

# ===============================
# MODEL & SENTIMENT CACHING (LAZY LOAD)
# ===============================
_model_cache = {}
_scaler_cache = {}
_finbert = None


def get_finbert():
    """Lazy load FinBERT model (memory optimization)"""
    global _finbert
    if _finbert is None:
        try:
            print("🔄 Loading FinBERT...")
            _finbert = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert"
            )
            print("✅ FinBERT loaded")
        except Exception as e:
            print(f"⚠️  FinBERT load failed: {e}")
            print("   Sentiment analysis will return 0")
            _finbert = None
    return _finbert


# ===============================
# INDICATORS
# ===============================
def add_indicators(df):
    """Add technical indicators to dataframe"""
    try:
        df["EMA"] = df["CLOSE"].ewm(span=14).mean()
        df["RETURNS"] = df["CLOSE"].pct_change()

        delta = df["CLOSE"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        loss = loss.replace(0, 1e-10)

        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        return df
    except Exception as e:
        raise ValueError(f"Error adding indicators: {str(e)}")


# ===============================
# DATA PREP
# ===============================
def prepare_dataframe(path):
    """Load and prepare data from CSV"""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
            
        df = pd.read_csv(path)
        df.columns = [c.upper() for c in df.columns]

        df["DATETIME"] = pd.to_datetime(df["DATE"] + " " + df["TIME"])
        df = df.sort_values("DATETIME").drop_duplicates("DATETIME")

        df = add_indicators(df).dropna()

        if df.empty:
            raise ValueError("DataFrame is empty after processing")

        return df
    except Exception as e:
        raise ValueError(f"Error preparing dataframe: {str(e)}")


# ===============================
# LOAD MODEL & SCALER (WITH CACHING)
# ===============================
def load_model_and_scaler(coin, mode):
    """Load model and scaler with memory caching"""
    cache_key = f"{coin}_{mode}"
    
    # Check cache
    if cache_key in _model_cache:
        print(f"📦 Using cached model for {cache_key}")
        return _model_cache[cache_key], _scaler_cache[cache_key]
    
    try:
        model_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_model.h5")
        scaler_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_scaler.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")

        print(f"📥 Loading model for {cache_key}")
        model = load_model(model_path, compile=False)
        scaler = joblib.load(scaler_path)
        
        # Store in cache
        _model_cache[cache_key] = model
        _scaler_cache[cache_key] = scaler
        
        return model, scaler
    except Exception as e:
        raise RuntimeError(f"Model loading failed for {coin} ({mode}): {str(e)}")


# ===============================
# SENTIMENT ANALYSIS
# ===============================
def get_news_sentiment(api_key, coin):
    """Fetch sentiment from CryptoPanic API using FinBERT"""
    url = "https://cryptopanic.com/api/developer/v2/posts/"

    try:
        if not api_key:
            print("⚠️  API key missing, skipping sentiment analysis")
            return 0

        res = requests.get(url, params={
            "auth_token": api_key,
            "currencies": coin,
            "public": "true"
        }, timeout=10)

        if res.status_code != 200:
            print(f"⚠️  CryptoPanic API error: {res.status_code}")
            return 0

        data = res.json()
        finbert = get_finbert()
        
        if finbert is None:
            return 0

        scores = []

        for post in data.get("results", [])[:10]:
            title = post.get("title", "")
            if not title:
                continue

            try:
                result = finbert(title)[0]

                if result["label"] == "positive":
                    scores.append(result["score"])
                elif result["label"] == "negative":
                    scores.append(-result["score"])
                else:
                    scores.append(0)
            except Exception as e:
                print(f"⚠️  Error analyzing sentiment: {e}")
                continue

        return sum(scores) / len(scores) if scores else 0

    except requests.exceptions.Timeout:
        print("⚠️  CryptoPanic API timeout, using default sentiment")
        return 0
    except Exception as e:
        print(f"⚠️  Sentiment analysis failed: {e}")
        return 0


def apply_sentiment(preds, score):
    """Apply sentiment adjustment to predictions"""
    factor = score * 0.05  # max ±5%
    return [[v * (1 + factor) for v in p] for p in preds]


# ===============================
# PREDICTION
# ===============================
def predict_future(coin, mode, steps):
    """Generate future price predictions"""
    try:
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
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {str(e)}")


# ===============================
# MAIN API FUNCTION
# ===============================
def run_prediction(coin, mode, steps):
    """Main prediction function with error handling"""
    try:
        if coin not in AVAILABLE_COINS:
            raise ValueError(f"Unsupported coin: {coin}. Available: {', '.join(AVAILABLE_COINS)}")

        if mode not in ["daily", "hourly"]:
            raise ValueError(f"Invalid mode: {mode}. Use 'daily' or 'hourly'")

        if not isinstance(steps, int) or steps < 1:
            raise ValueError(f"Invalid steps: {steps}. Must be positive integer")

        print(f"\n🔮 Predicting {coin} ({mode}) for {steps} steps...")

        preds = predict_future(coin, mode, steps)
        coin_symbol = coin.split("-")[0]
        sentiment = get_news_sentiment(CRYPTOPANIC_API_KEY, coin_symbol)

        preds = apply_sentiment(preds, sentiment)
        final = preds[-1]

        result = {
            "coin": coin,
            "mode": mode,
            "sentiment": float(sentiment),
            "open": float(final[0]),
            "high": float(final[1]),
            "low": float(final[2]),
            "close": float(final[3])
        }
        
        print(f"✅ Prediction complete: {result}")
        return result

    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        raise
