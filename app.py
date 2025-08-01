from flask import Flask, render_template, jsonify
from predictor import predict_next_numbers, summary_stats
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

CSV_PATH = "data/ga_cash3_history.csv"

def load_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found")
    df = pd.read_csv(CSV_PATH)
    if df.empty:
        raise ValueError("CSV is empty")
    return df

@app.route('/')
def index():
    try:
        df = load_data()
    except Exception as e:
        return render_template("index.html", error=f"Error loading data: {e}")

    latest = df.iloc[0]
    predictions = predict_next_numbers(df)
    draw_specific = {
        "Midday": predict_next_numbers(df, draw="Midday"),
        "Evening": predict_next_numbers(df, draw="Evening"),
        "Night": predict_next_numbers(df, draw="Night"),
    }
    # last updated (file mtime)
    updated_ts = datetime.fromtimestamp(os.path.getmtime(CSV_PATH)).strftime("%Y-%m-%d %H:%M:%S")

    stats = summary_stats(df)
    return render_template(
        "index.html",
        latest=latest,
        predictions=predictions,
        draw_specific=draw_specific,
        stats=stats,
        updated=updated_ts,
    )

@app.route('/api/summary')
def api_summary():
    try:
        df = load_data()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    stats = summary_stats(df)
    return jsonify({
        "summary": stats,
        "last_updated": datetime.fromtimestamp(os.path.getmtime(CSV_PATH)).isoformat(),
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
