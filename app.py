# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from predictor import predict_next_numbers, top_triplets, digit_frequency, hot_cold
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this")  # for flash messages

CSV_PATH = "data/ga_cash3_history.csv"
STATUS_PATH = "data/.status.json"

def load_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found")
    df = pd.read_csv(CSV_PATH)
    # Force types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

def load_status():
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH, "r") as f:
            return json.load(f)
    return {}

@app.route("/", methods=["GET"])
def index():
    draw_filter = request.args.get("draw")  # Midday / Evening / Night
    try:
        df = load_data()
    except Exception as e:
        return render_template("index.html", error=str(e), latest=None)

    # Optionally filter by draw type for history/predictions
    filtered = df if not draw_filter else df[df["Draw"].str.lower() == draw_filter.lower()]

    latest = df.iloc[0] if not df.empty else None
    predictions = predict_next_numbers(df, draw_filter)
    top = top_triplets(df, draw_filter, n=5)
    digit_freqs = digit_frequency(df, draw_filter)
    hc = hot_cold(df, draw_filter)

    status = load_status()

    return render_template(
        "index.html",
        latest=latest,
        predictions=predictions,
        top_triplets=top,
        digit_freqs=digit_freqs,
        hot_cold=hc,
        draw_filter=draw_filter,
        status=status,
    )

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("index"))
    f = request.files["file"]
    if f.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("index"))
    try:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        f.save(CSV_PATH)
        flash("CSV uploaded successfully.", "success")
    except Exception as e:
        flash(f"Failed to upload: {e}", "error")
    return redirect(url_for("index"))

@app.route("/add_draw", methods=["POST"])
def add_draw():
    date = request.form.get("date")
    draw = request.form.get("draw")
    draw_time = request.form.get("draw_time")
    d1 = request.form.get("digit1")
    d2 = request.form.get("digit2")
    d3 = request.form.get("digit3")
    try:
        new = {
            "Date": pd.to_datetime(date).date().isoformat(),
            "Draw": draw,
            "DrawTime": draw_time,
            "Digit1": int(d1),
            "Digit2": int(d2),
            "Digit3": int(d3),
        }
        # append manually
        df = pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame(columns=new.keys())
        exists = df[(df["Date"] == new["Date"]) & (df["Draw"] == new["Draw"])]
        if not exists.empty:
            flash("Draw already exists, skipping.", "info")
        else:
            df = pd.concat([pd.DataFrame([new]), df], ignore_index=True)
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            df.sort_values(by=["Date", "Draw"], ascending=[False, False], inplace=True)
            df.to_csv(CSV_PATH, index=False)
            flash("Draw added.", "success")
    except Exception as e:
        flash(f"Failed to add draw: {e}", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
