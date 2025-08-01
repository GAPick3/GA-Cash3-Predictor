from flask import Flask, render_template
import pandas as pd
import os
import json

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
        with open(SUMMARY_PATH) as f:
            return json.load(f)
    return {}

@app.route("/")
def index():
    error = None
    latest = None
    summary = load_summary()
    try:
        df = load_data()
        if not df.empty:
            # assume sorted descending
            latest = df.iloc[0].to_dict()
    except Exception as e:
        error = f"Error loading data: {e}"
    return render_template("index.html", latest=latest, summary=summary, error=error)
