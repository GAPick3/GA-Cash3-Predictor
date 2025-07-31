from flask import Flask, render_template, jsonify
import pandas as pd
import os
from predictor import predict_next_numbers

app = Flask(__name__)
CSV_PATH = "data/ga_cash3_history.csv"

def load_data():
    if not os.path.exists(CSV_PATH):
        # return empty frame to avoid throwing later
        cols = ["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"]
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
    df.rename(columns=lambda c: c.strip(), inplace=True)
    if "Date" in df.columns:
        df.sort_values(["Date", "Draw"], ascending=[False, True], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

@app.route('/')
def index():
    try:
        df = load_data()
    except Exception as e:
        return render_template("index.html", error=f"Error loading data: {e}", latest=None, predictions=None, recent_draws=[])

    if df.empty:
        return render_template("index.html", error="No draw data available.", latest=None, predictions=None, recent_draws=[])

    latest_row = df.iloc[0]
    latest = {
        "Date": latest_row["Date"].strftime("%Y-%m-%d") if not pd.isna(latest_row["Date"]) else "",
        "Draw": latest_row.get("Draw", ""),
        "DrawTime": latest_row.get("DrawTime", ""),
        "Digit1": int(latest_row["Digit1"]) if pd.notna(latest_row.get("Digit1", None)) else "",
        "Digit2": int(latest_row["Digit2"]) if pd.notna(latest_row.get("Digit2", None)) else "",
        "Digit3": int(latest_row["Digit3"]) if pd.notna(latest_row.get("Digit3", None)) else "",
    }

    predictions = predict_next_numbers(df)
    disclaimer = (
        "Cash 3 draws are independent. Historical frequency does not guarantee future results. "
        "Use the combinations for informational purposes only."
    )

    recent_draws = []
    for _, r in df.head(10).iterrows():
        recent_draws.append({
            "Date": r["Date"].strftime("%Y-%m-%d") if not pd.isna(r["Date"]) else "",
            "Draw": r.get("Draw", ""),
            "DrawTime": r.get("DrawTime", ""),
            "Digit1": int(r["Digit1"]) if pd.notna(r.get("Digit1")) else "",
            "Digit2": int(r["Digit2"]) if pd.notna(r.get("Digit2")) else "",
            "Digit3": int(r["Digit3"]) if pd.notna(r.get("Digit3")) else "",
        })

    return render_template(
        "index.html",
        latest=latest,
        predictions=predictions,
        disclaimer=disclaimer,
        recent_draws=recent_draws,
    )

@app.route('/health')
def health():
    try:
        df = load_data()
        last_date = df.iloc[0]["Date"] if not df.empty else None
        return jsonify({
            "status": "ok" if not df.empty else "no_data",
            "rows": len(df),
            "latest_draw_date": str(last_date.date()) if last_date is not None else None
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/predictions')
def api_predictions():
    try:
        df = load_data()
        return jsonify(predict_next_numbers(df))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
