from flask import Flask, render_template
import pandas as pd
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    csv_path = 'data/ga_cash3_history_cleaned.csv'
    pred_path = 'static/last_prediction.json'
    acc_path = 'static/accuracy_history.json'

    if not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0:
        return render_template("index.html", error="History data not available.")

    df = pd.read_csv(csv_path)
    if df.empty:
        return render_template("index.html", error="No draw data found.")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values(by='Date')
    latest = df.iloc[-1].to_dict()

    prediction = [0, 0, 0]
    if os.path.exists(pred_path):
        with open(pred_path) as f:
            prediction = json.load(f)

    last_prediction = prediction
    accuracy_data = []
    summary = {"total": 0, "exact": 0, "any_order": 0}

    if os.path.exists(acc_path):
        with open(acc_path) as f:
            accuracy_data = json.load(f)
            summary["total"] = len(accuracy_data)
            summary["exact"] = sum(1 for m in accuracy_data if m["match"] == "Exact")
            summary["any_order"] = sum(1 for m in accuracy_data if m["match"] == "AnyOrder")

    return render_template("index.html",
                           latest_result=latest,
                           prediction=prediction,
                           last_prediction=last_prediction,
                           accuracy=summary,
                           accuracy_history=accuracy_data)
