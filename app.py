from flask import Flask, render_template, jsonify
import pandas as pd
import os
from predictor import predict_next_numbers

app = Flask(__name__)
CSV_PATH = "data/ga_cash3_history.csv"

def load_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found")
    df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
    # Normalize header whitespace
    df.rename(columns=lambda c: c.strip(), inplace=True)
    # Ensure sorting: newest first
    df.sort_values(["Date", "Draw"], ascending=[False, True], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

@app.route('/')
def index():
    try:
        df = load_data()
        if df.empty:
            return render_template("index.html", error="No draw data found.")
    except Exception as e:
        return render_template("index.html", error=f"Error loading data: {e}")

    latest = df.iloc[0]
    prediction_summary = predict_next_numbers(df)
    disclaimer = (
        "Cash 3 draws are independent. Historical frequency does not guarantee future results. "
        "Use the combinations for informational purposes only."
    )

    # Pass structured predictions to template
    return render_template(
        "index.html",
        latest=latest,
        predictions=prediction_summary,
        disclaimer=disclaimer,
        recent_draws=df.head(10).to_dict(orient="records"),
    )

@app.route('/api/latest')
def api_latest():
    try:
        df = load_data()
        return jsonify(df.iloc[0].to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictions')
def api_predictions():
    try:
        df = load_data()
        summary = predict_next_numbers(df)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    try:
        df = load_data()
        last_date = df.iloc[0]["Date"]
        count = len(df)
        return jsonify({
            "status": "ok",
            "rows": count,
            "latest_draw_date": str(last_date)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
