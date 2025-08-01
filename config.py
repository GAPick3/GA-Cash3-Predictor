# config.py
from pathlib import Path

# Data paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORY_CSV = DATA_DIR / "ga_cash3_history.csv"
LATEST_HTML = DATA_DIR / "latest.htm"
LATEST_PDF = DATA_DIR / "latest.pdf"
SUMMARY_JSON = DATA_DIR / "summary.json"

# Fallback PDF URL (set to the authoritative source; update if it changes)
PDF_URL = "https://example.com/path/to/latest.pdf"  # <-- replace with real PDF link

# Known draw times (ET)
DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}
