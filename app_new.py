from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
import time
from datetime import datetime
import os

from check import run_prediction

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# =========================
# CONFIG
# =========================

COINS = [
    "BTC", "ETH", "BNB", "SOL",
    "DOT", "XRP", "TRX", "DOGE",
    "ADA", "MATIC"
]

prediction_progress = {}

# =========================
# FRONTEND ROUTES
# =========================

@app.route("/")
def index():
    try:
        return send_from_directory("frontend", "index.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/<path:path>")
def serve_files(path):
    try:
        return send_from_directory("frontend", path)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404


# =========================
# PREDICTION API
# =========================

@app.route("/api/predict", methods=["POST"])
def predict():
    """
    POST endpoint for crypto price predictions
    Expected JSON: {"symbol": "BTC", "mode": "daily|hourly", "timeframe": 24}
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400

        symbol = data.get("symbol")
        mode = data.get("mode")
        timeframe = data.get("timeframe")

        # ✅ VALIDATION
        if symbol not in COINS:
            return jsonify({
                "success": False,
                "error": f"Invalid coin. Supported: {', '.join(COINS)}"
            }), 400

        if mode not in ["daily", "hourly"]:
            return jsonify({
                "success": False,
                "error": "Invalid mode. Use 'daily' or 'hourly'"
            }), 400

        if not isinstance(timeframe, int) or timeframe < 1:
            return jsonify({
                "success": False,
                "error": "Invalid timeframe. Must be positive integer"
            }), 400

        prediction_id = str(int(time.time() * 1000))

        prediction_progress[prediction_id] = {
            "status": "processing"
        }

        # =========================
        # BACKGROUND THREAD
        # =========================
        def run_real_prediction():
            try:
                coin = f"{symbol}-INR"
                result = run_prediction(coin, mode, timeframe)

                prediction_progress[prediction_id] = {
                    "status": "complete",
                    "prediction": {
                        "open": float(result["open"]),
                        "high": float(result["high"]),
                        "low": float(result["low"]),
                        "close": float(result["close"]),
                        "sentiment": float(result.get("sentiment", 0))
                    }
                }

            except Exception as e:
                prediction_progress[prediction_id] = {
                    "status": "error",
                    "message": f"Prediction failed: {str(e)}"
                }

        threading.Thread(target=run_real_prediction, daemon=True).start()

        return jsonify({
            "success": True,
            "prediction_id": prediction_id
        }), 202

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


# =========================
# PROGRESS API
# =========================

@app.route("/api/progress/<prediction_id>")
def progress(prediction_id):
    """Check prediction progress"""
    try:
        if prediction_id in prediction_progress:
            return jsonify(prediction_progress[prediction_id]), 200

        return jsonify({
            "status": "unknown",
            "error": "Prediction ID not found"
        }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# HEALTH CHECK
# =========================

@app.route("/api/health")
def health():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "running",
            "time": datetime.now().isoformat(),
            "version": "1.0",
            "supported_coins": COINS
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ERROR HANDLERS
# =========================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 CryptoForeCast Server Starting")
    print(f"   Port: {port}")
    print(f"   Debug: {debug_mode}")
    print(f"   Host: 0.0.0.0")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode
    )
