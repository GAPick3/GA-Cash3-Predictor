import json
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

def load_summary():
    try:
        with open("data/summary.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.warning("summary.json not found")
        return {}
    except json.JSONDecodeError:
        app.logger.warning("summary.json malformed")
        return {}

def load_history():
    try:
        df = pd.read_csv("data/ga_cash3_history.csv")
        return df.to_dict(orient="records")
    except FileNotFoundError:
        app.logger.warning("history CSV not found")
        return []
    except Exception as e:
        app.logger.warning(f"failed to load history: {e}")
        return []

@app.route("/")
def index():
    summary = load_summary()
    predictions = summary.get("predictions") or summary.get("simple_insights", {})
    latest = summary.get("latest_draw", {})
    history = load_history()
    return render_template(
        "index.html",
        latest=latest,
        summary=summary,
        history=history,
        predictions=predictions,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
