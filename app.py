import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def health():
    try:
        return jsonify({"status": "CryptoForecast running"}), 200
    except Exception as exc:
        return jsonify({"error": "Internal server error", "details": str(exc)}), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
