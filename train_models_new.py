import os
import pandas as pd
import numpy as np
import threading
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import joblib

# ===============================
# CONFIG
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "models")

TIME_STEPS = 60
EPOCHS = 10
BATCH_SIZE = 32

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ===============================
# INDICATORS
# ===============================
def add_indicators(df):
    """Add technical indicators for feature engineering"""
    try:
        # EMA
        df["EMA"] = df["CLOSE"].ewm(span=14).mean()

        # Returns
        df["RETURNS"] = df["CLOSE"].pct_change()

        # RSI
        delta = df["CLOSE"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        return df
    except Exception as e:
        raise ValueError(f"Error adding indicators: {str(e)}")


# ===============================
# LOAD + PREPROCESS
# ===============================
def load_and_preprocess(file_path):
    """Load data from CSV and preprocess for LSTM training"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        print(f"📥 Loading {file_path}...")
        df = pd.read_csv(file_path)

        df.columns = [col.upper() for col in df.columns]

        required_cols = ["DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"{col} missing in {file_path}")

        # Combine datetime
        df["DATETIME"] = pd.to_datetime(df["DATE"] + " " + df["TIME"])

        # Sort + clean
        df = df.sort_values("DATETIME")
        df = df.drop_duplicates(subset=["DATETIME"])

        print(f"   Data points: {len(df)}")

        # Add indicators
        df = add_indicators(df)

        # Drop NaN rows (due to indicators)
        df = df.dropna()

        print(f"   After processing: {len(df)}")

        # Features (OHLC + indicators)
        feature_cols = ["OPEN", "HIGH", "LOW", "CLOSE", "EMA", "RSI", "RETURNS"]

        data = df[feature_cols].astype(float).values

        # Normalize
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data)

        # Create sequences
        X, y = [], []
        for i in range(TIME_STEPS, len(scaled_data)):
            X.append(scaled_data[i - TIME_STEPS:i])
            y.append(scaled_data[i][:4])  # Only predict OHLC

        return np.array(X), np.array(y), scaler
    except Exception as e:
        raise RuntimeError(f"Error loading/preprocessing {file_path}: {str(e)}")


# ===============================
# MODEL
# ===============================
def build_model(input_shape):
    """Build LSTM model for price prediction"""
    try:
        model = Sequential()
        model.add(LSTM(64, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(64))
        model.add(Dense(32, activation="relu"))
        model.add(Dense(4))  # OPEN, HIGH, LOW, CLOSE
        model.compile(optimizer="adam", loss="mean_squared_error")
        return model
    except Exception as e:
        raise RuntimeError(f"Error building model: {str(e)}")


# ===============================
# TRAIN
# ===============================
def train_model(coin, mode):
    """Train LSTM model for a specific coin and timeframe"""
    try:
        # Load data
        data_file = os.path.join(DATA_DIR, mode, f"{coin}_{mode}.csv")
        X, y, scaler = load_and_preprocess(data_file)

        # Model
        model = build_model((X.shape[1], X.shape[2]))

        print(f"\n🚀 Training {coin} ({mode}) model...")
        print(f"   Input shape: {X.shape}")
        print(f"   Output shape: {y.shape}")

        # Train
        history = model.fit(
            X, y,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_split=0.2,
            verbose=0
        )

        # Save
        model_dir = os.path.join(OUTPUT_DIR, mode)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, f"{coin}_{mode}_model.h5")
        scaler_path = os.path.join(model_dir, f"{coin}_{mode}_scaler.pkl")

        model.save(model_path)
        joblib.dump(scaler, scaler_path)

        print(f"✅ Model saved: {model_path}")
        print(f"✅ Scaler saved: {scaler_path}")
        print(f"   Final loss: {history.history['loss'][-1]:.6f}")

        return True

    except Exception as e:
        print(f"❌ Error training {coin} ({mode}): {str(e)}")
        return False


# ===============================
# TRAIN ALL
# ===============================
COINS = [
    "BTC-INR", "ETH-INR", "BNB-INR", "SOL-INR",
    "DOT-INR", "XRP-INR", "TRX-INR", "DOGE-INR",
    "ADA-INR", "MATIC-INR"
]

MODES = ["daily", "hourly"]


def train_all_models():
    """Train all models for all coins and modes"""
    print("\n" + "="*50)
    print("🤖 TRAINING ALL MODELS")
    print("="*50)

    total = len(COINS) * len(MODES)
    success = 0

    for mode in MODES:
        print(f"\n📊 Mode: {mode.upper()}")
        print("-" * 50)

        for coin in COINS:
            if train_model(coin, mode):
                success += 1

    print("\n" + "="*50)
    print(f"✅ Training Complete: {success}/{total} models trained successfully")
    print("="*50 + "\n")


if __name__ == "__main__":
    train_all_models()
