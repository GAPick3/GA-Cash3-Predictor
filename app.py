# app.py

from flask import Flask, render_template, request
import pandas as pd
import json
import os
from predictor import predict_next_numbers

app = Flask(__name__)

CSV_PATH = "data/ga_cash3_history.csv"
SUMMARY_PATH = "data/summary.json"

def load_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found")
    df = pd.read_csv(CSV_PATH)
    return df

def load_summary():
    if os.path.exists(SUMMARY_PATH):
        try:
            with open(SUMMARY_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

@app.route('/')
def index():
    error = None
    df = None
    summary = {}
    latest = None
    predictions = []

    draw_filter = request.args.get("draw")  # optional ?draw=Midday

    try:
        df = load_data()
        if df.empty:
            error = "No data available."
        else:
            # Ensure proper formatting
            df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
            latest = df.iloc[0]
            predictions = predict_next_numbers(df, draw=draw_filter, n=5)
            summary = load_summary()
    except Exception as e:
        error = f"Error loading data: {e}"

    return render_template(
        "index.html",
        latest=latest,
        predictions=predictions,
        summary=summary,
        draw_filter=draw_filter,
        error=error,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
