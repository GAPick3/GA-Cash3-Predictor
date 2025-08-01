import os
import threading
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import json

from pathlib import Path
from prepare_data import HISTORY_CSV, SUMMARY_JSON, main as prepare_main  # refactor prepare_data to be importable

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me")  # for flash messages

# Simple in-memory cache to avoid reloading CSV on every request
_cache = {
    "history": None,
    "last_loaded": None,
    "summary": None,
}


def load_history():
    if _cache["history"] is None or not HISTORY_CSV.exists():
        try:
            df = pd.read_csv(HISTORY_CSV, parse_dates=["Date"])
        except Exception:
            df = pd.DataFrame()
        _cache["history"] = df
    return _cache["history"]


def load_summary():
    if _cache["summary"] is None or not SUMMARY_JSON.exists():
        try:
            with open(SUMMARY_JSON, encoding="utf-8") as f:
                _cache["summary"] = json.load(f)
        except Exception:
            _cache["summary"] = {}
    return _cache["summary"]


@app.route("/", methods=["GET"])
def index():
    summary = load_summary()
    history = load_history()
    latest = summary.get("latest") if summary else None
    return render_template("index.html", latest=latest, summary=summary, history=history)


@app.route("/upload", methods=["POST"])
def upload():
    """
    Upload a new latest.pdf or latest.htm to override source. Then rebuild.
    """
    if "file" not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("index"))
    file = request.files["file"]
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("index"))
    # Determine type
    filename = file.filename.lower()
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    if filename.endswith(".pdf"):
        target = data_dir / "latest.pdf"
    elif filename.endswith(".htm") or filename.endswith(".html"):
        target = data_dir / "latest.htm"
    else:
        flash("Unsupported file type; please upload .pdf or .htm/.html", "warning")
        return redirect(url_for("index"))
    file.save(target)
    flash(f"Uploaded {file.filename}, reprocessing data...", "success")

    # Trigger prepare_data in separate thread to avoid blocking UI
    def run_prep():
        try:
            prepare_main()
            # Invalidate cache
            _cache["history"] = None
            _cache["summary"] = None
        except Exception as e:
            app.logger.exception("Rebuild after upload failed: %s", e)
    threading.Thread(target=run_prep, daemon=True).start()

    return redirect(url_for("index"))


# Optional: endpoint to manually trigger refresh
@app.route("/refresh", methods=["POST"])
def refresh():
    threading.Thread(target=lambda: (prepare_main(), _cache.clear()), daemon=True).start()
    flash("Triggered data refresh in background.", "info")
    return redirect(url_for("index"))
