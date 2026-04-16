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


# ===============================
# INDICATORS
# ===============================
def add_indicators(df):
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


# ===============================
# LOAD + PREPROCESS
# ===============================
def load_and_preprocess(file_path):
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

    # Add indicators
    df = add_indicators(df)

    # Drop NaN rows (due to indicators)
    df = df.dropna()

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


# ===============================
# MODEL
# ===============================
def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(64))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(4))  # OPEN, HIGH, LOW, CLOSE
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


# ===============================
# TRAIN + SAVE
# ===============================
def train_and_save(file_path, mode):
    try:
        coin_name = os.path.basename(file_path).replace(".csv", "")

        print(f"[INFO] Training {coin_name} ({mode})")

        X, y, scaler = load_and_preprocess(file_path)

        if len(X) < 100:
            print(f"[SKIP] Not enough data for {coin_name}")
            return

        model = build_model((X.shape[1], X.shape[2]))

        model.fit(
            X, y,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            verbose=1
        )

        # Save model
        model_path = os.path.join(
            OUTPUT_DIR, mode, f"{coin_name}_model.h5"
        )
        model.save(model_path)

        # Save scaler
        scaler_path = os.path.join(
            OUTPUT_DIR, mode, f"{coin_name}_scaler.pkl"
        )
        joblib.dump(scaler, scaler_path)

        print(f"[SUCCESS] Saved {coin_name}")

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")


# ===============================
# TRAIN ALL
# ===============================
def train_all_models():
    threads = []

    # DAILY
    daily_path = os.path.join(DATA_DIR, "daily")
    for file in os.listdir(daily_path):
        if file.endswith(".csv"):
            file_path = os.path.join(daily_path, file)

            t = threading.Thread(
                target=train_and_save,
                args=(file_path, "daily")
            )
            threads.append(t)
            t.start()

    # HOURLY
    hourly_path = os.path.join(DATA_DIR, "hourly")
    for file in os.listdir(hourly_path):
        if file.endswith(".csv"):
            file_path = os.path.join(hourly_path, file)

            t = threading.Thread(
                target=train_and_save,
                args=(file_path, "hourly")
            )
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    print("🚀 All models trained successfully!")


if __name__ == "__main__":
    train_all_models()