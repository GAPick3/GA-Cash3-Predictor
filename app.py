import json
import pandas as pd
import os
from flask import Flask, render_template

app = Flask(__name__)

SUMMARY_PATH = os.path.join("data", "summary.json")
HISTORY_PATH = os.path.join("data", "ga_cash3_history.csv")

def load_summary(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        app.logger.warning("summary.json malformed or unreadable: %s", e)
        return {}

def load_history(path):
    try:
        df = pd.read_csv(path)
        # Optional: coerce digit columns to int if possible, else leave as-is
        for col in ["Digit1", "Digit2", "Digit3"]:
            if col in df.columns:
                # convert float-ish to int where appropriate, preserve NaN as None
                df[col] = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        app.logger.warning("failed to load history: %s", e)
        return []

def pick_latest(history):
    if not history:
        return None
    try:
        df = pd.DataFrame(history)
        # Parse date if possible; fall back to list order
        if "Date" in df.columns:
            df["__parsed_date"] = pd.to_datetime(df["Date"], errors="coerce")
            # If Draw exists, sort secondary
            sort_keys = ["__parsed_date"]
            if "Draw" in df.columns:
                sort_keys.append("Draw")
            df = df.sort_values(by=sort_keys, ascending=[False] * len(sort_keys))
            latest_row = df.iloc[0].to_dict()
        else:
            latest_row = history[-1]
        # Clean internal helper column
        latest_row.pop("__parsed_date", None)
        return latest_row
    except Exception:
        return history[-1]

def normalize_predictions(summary):
    preds = summary.get("predictions", {})
    common = preds.get("common", {})
    uncommon = preds.get("uncommon", {})

    def ensure_digits(d):
        return {
            "Digit1": d.get("Digit1", "N/A"),
            "Digit2": d.get("Digit2", "N/A"),
            "Digit3": d.get("Digit3", "N/A"),
        }

    return {
        "common": ensure_digits(common),
        "uncommon": ensure_digits(uncommon),
    }

@app.route("/")
def index():
    summary = load_summary(SUMMARY_PATH)
    history = load_history(HISTORY_PATH)
    latest = pick_latest(history)
    predictions = normalize_predictions(summary)

    # Ensure top-level fallback fields exist
    summary.setdefault("total_draws", len(history))
    # Optionally format last_updated if it's a datetime string — leave as-is for template.

    return render_template(
        "index.html",
        summary=summary,
        history=history,
        latest=latest,
        predictions=predictions,
    )
