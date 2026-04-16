import os
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TIME_STEPS = 60
FEATURE_COLS = ["OPEN", "HIGH", "LOW", "CLOSE", "EMA", "RSI", "RETURNS"]
VALID_MODES = ["daily", "hourly"]
AVAILABLE_COINS = [
    "BTC-INR", "ETH-INR", "BNB-INR", "SOL-INR",
    "DOT-INR", "XRP-INR", "TRX-INR", "DOGE-INR",
    "ADA-INR", "MATIC-INR",
]

# Lazy caches (models/scalers are loaded only when first requested)
MODEL_CACHE: Dict[Tuple[str, str], object] = {}
SCALER_CACHE: Dict[Tuple[str, str], object] = {}


def _normalize_coin(symbol: str) -> str:
    """Accept BTC or BTC-INR and normalize to BTC-INR."""
    symbol = str(symbol or "").upper().strip()
    if not symbol:
        raise ValueError("symbol is required")
    return symbol if symbol.endswith("-INR") else f"{symbol}-INR"


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df["EMA"] = df["CLOSE"].ewm(span=14).mean()
    df["RETURNS"] = df["CLOSE"].pct_change()

    delta = df["CLOSE"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean().replace(0, 1e-10)
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def _prepare_dataframe(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Data file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [c.upper() for c in df.columns]

    required = ["DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")

    df["DATETIME"] = pd.to_datetime(df["DATE"].astype(str) + " " + df["TIME"].astype(str), errors="coerce")
    df = df.dropna(subset=["DATETIME"]).sort_values("DATETIME").drop_duplicates("DATETIME")
    df = _add_indicators(df).dropna()

    if df.empty:
        raise ValueError("No usable rows after preprocessing")

    return df


def _load_model_and_scaler(coin: str, mode: str):
    """Lazy-load and cache model/scaler for a coin+mode."""
    key = (coin, mode)
    if key in MODEL_CACHE and key in SCALER_CACHE:
        return MODEL_CACHE[key], SCALER_CACHE[key]

    model_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_model.h5")
    scaler_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_scaler.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    # Import TensorFlow only at load time to avoid startup overhead.
    from tensorflow.keras.models import load_model

    model = load_model(model_path, compile=False)
    scaler = joblib.load(scaler_path)

    MODEL_CACHE[key] = model
    SCALER_CACHE[key] = scaler
    return model, scaler


def _find_first_model_pair():
    """Return the first available coin/mode pair that has both model and scaler files."""
    for coin in AVAILABLE_COINS:
        for mode in VALID_MODES:
            model_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_model.h5")
            scaler_path = os.path.join(MODEL_DIR, mode, f"{coin}_{mode}_scaler.pkl")
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                return coin, mode
    return None


def _predict_future(coin: str, mode: str, steps: int):
    csv_path = os.path.join(DATA_DIR, mode, f"{coin}_{mode}.csv")
    model, scaler = _load_model_and_scaler(coin, mode)
    df = _prepare_dataframe(csv_path)

    data = df[FEATURE_COLS].astype(float).values
    scaled = scaler.transform(data)
    if len(scaled) < TIME_STEPS:
        raise ValueError(f"Not enough rows in data for TIME_STEPS={TIME_STEPS}")

    sequence = scaled.copy()
    predictions = []

    for _ in range(steps):
        x_input = sequence[-TIME_STEPS:].reshape(1, TIME_STEPS, len(FEATURE_COLS))
        pred_scaled = model.predict(x_input, verbose=0)

        temp = np.zeros((1, len(FEATURE_COLS)))
        temp[0, :4] = pred_scaled[0]
        pred_real = scaler.inverse_transform(temp)[0]
        predictions.append(pred_real[:4])

        new_row = np.zeros(len(FEATURE_COLS))
        new_row[:4] = pred_scaled[0]
        sequence = np.vstack([sequence, new_row])

    return predictions


@app.route("/")
def health():
    return jsonify({"status": "CryptoForecast running"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(silent=True) or {}
        coin = _normalize_coin(payload.get("symbol"))
        mode = str(payload.get("mode", "daily")).lower().strip()
        steps = int(payload.get("timeframe", 1))

        if coin not in AVAILABLE_COINS:
            return jsonify({"error": f"Unsupported coin: {coin}"}), 400
        if mode not in VALID_MODES:
            return jsonify({"error": f"Invalid mode: {mode}. Use daily or hourly"}), 400
        if steps < 1:
            return jsonify({"error": "timeframe must be >= 1"}), 400

        preds = _predict_future(coin, mode, steps)
        final = preds[-1]

        return jsonify(
            {
                "coin": coin,
                "mode": mode,
                "timeframe": steps,
                "prediction": {
                    "open": float(final[0]),
                    "high": float(final[1]),
                    "low": float(final[2]),
                    "close": float(final[3]),
                },
            }
        ), 200

    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": "Prediction failed", "details": str(exc)}), 500


@app.route("/test-model")
def test_model():
    """Loads one available model/scaler to verify runtime compatibility."""
    try:
        pair = _find_first_model_pair()

        if pair is not None:
            coin, mode = pair
            _load_model_and_scaler(coin, mode)
            return "Model loaded successfully", 200

        return jsonify({"error": "No model/scaler pair found under models/"}), 404
    except Exception as exc:
        return jsonify({"error": "Model load failed", "details": str(exc)}), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
