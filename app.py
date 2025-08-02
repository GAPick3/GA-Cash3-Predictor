from flask import Flask, render_template
import json
import pandas as pd
import logging

app = Flask(__name__)
logger = app.logger

def load_summary():
    try:
        with open("data/summary.json") as f:
            summary = json.load(f)
    except Exception as e:
        logger.warning("summary.json malformed or missing: %s", e)
        summary = {}
    return summary

def load_history():
    try:
        history = pd.read_csv("data/ga_cash3_history.csv")
    except Exception as e:
        logger.warning("failed to load history: %s", e)
        history = pd.DataFrame()
    return history

@app.route("/")
def index():
    summary = load_summary()
    history = load_history()

    # Provide safe defaults so template doesn't blow up
    predictions = summary.get("predictions", {})
    common = predictions.get("common", {"Digit1": "N/A", "Digit2": "N/A", "Digit3": "N/A"})
    uncommon = predictions.get("uncommon", {"Digit1": "N/A", "Digit2": "N/A", "Digit3": "N/A"})
    preds = {
        "common": common,
        "uncommon": uncommon,
    }

    latest = summary.get("latest_draw", {})
    return render_template(
        "index.html",
        latest=latest,
        summary=summary,
        history=history.to_dict(orient="records") if not history.empty else [],
        predictions=preds,
    )
