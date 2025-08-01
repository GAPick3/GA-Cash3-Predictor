import os
import sys
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup  # kept only if you want to parse latest.htm fallback

# Configuration (can be overridden via env)
PDF_URL = os.environ.get("PDF_URL", "https://www.lotterypost.com/results/georgia/cash-3/download")
HISTORY_CSV = Path("data/ga_cash3_history.csv")
SUMMARY_JSON = Path("data/summary.json")
LOCAL_PDF = Path("data/latest.pdf")
LOCAL_HTML = Path("data/latest.htm")
MAX_FETCH_ATTEMPTS = 3
BACKOFF_BASE = 2  # exponential

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def download_pdf(target: Path) -> bool:
    """Attempt to fetch the PDF with retry/backoff. Returns True if successful."""
    headers_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        # could add others if needed
    ]
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        ua = headers_list[(attempt - 1) % len(headers_list)]
        headers = {
            "User-Agent": ua,
            "Accept": "application/pdf,application/octet-stream",
        }
        try:
            logger.info("Downloading latest PDF from %s (attempt %d) with UA=%s", PDF_URL, attempt, ua)
            resp = requests.get(PDF_URL, headers=headers, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not resp.content.startswith(b"%PDF"):
                logger.warning("Response does not look like a PDF (Content-Type=%s)", content_type)
            target.write_bytes(resp.content)
            logger.info("PDF downloaded and saved to %s", target)
            return True
        except requests.HTTPError as e:
            logger.warning("Fetch attempt %d failed: %s", attempt, e)
        except Exception as e:
            logger.warning("Unexpected error on attempt %d fetching PDF: %s", attempt, e)
        sleep = BACKOFF_BASE ** (attempt - 1)
        time.sleep(sleep)
    logger.error("All PDF fetch attempts failed.")
    return False


def parse_pdf(pdf_path: Path) -> pd.DataFrame:
    """Parse draws from the provided PDF. Returns DataFrame of new draws."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"{pdf_path} does not exist for parsing.")
    draws = []
    with pdfplumber.open(pdf_path) as pdf:
        # This will need to be tailored to actual PDF layout; placeholder logic:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Example parsing: look for lines with date + draw + digits
        for line in lines:
            # naive example: "07/25/2025 Night 3 7 7"
            parts = line.split()
            if len(parts) >= 5:
                date_str, draw_time = parts[0], parts[1]
                digits = parts[2:5]
                try:
                    date = datetime.strptime(date_str, "%m/%d/%Y").date()
                    d1, d2, d3 = [int(d) for d in digits]
                    draws.append({
                        "Date": pd.to_datetime(date),
                        "DrawTime": draw_time,
                        "Digit1": d1,
                        "Digit2": d2,
                        "Digit3": d3,
                    })
                except Exception:
                    continue  # skip lines that don't match
    if not draws:
        logger.warning("No draws parsed from PDF %s", pdf_path)
        return pd.DataFrame()
    df = pd.DataFrame(draws)
    # Normalize types
    df["Digit1"] = df["Digit1"].astype(int)
    df["Digit2"] = df["Digit2"].astype(int)
    df["Digit3"] = df["Digit3"].astype(int)
    # If needed, create a canonical unique key
    df["DrawKey"] = df["Date"].dt.strftime("%Y-%m-%d") + "_" + df["DrawTime"]
    return df


def parse_html_fallback(html_path: Path) -> pd.DataFrame:
    """Optional: parse latest.htm when PDF fetch fails."""
    if not html_path.exists():
        return pd.DataFrame()
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # Implementation depends on HTML structure; placeholder
    # For example, find table rows and extract date/time/digits
    draws = []
    for row in soup.select("table tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 5:
            date_str, draw_time = cols[0], cols[1]
            digits = cols[2:5]
            try:
                date = datetime.strptime(date_str, "%m/%d/%Y").date()
                d1, d2, d3 = [int(d) for d in digits]
                draws.append({
                    "Date": pd.to_datetime(date),
                    "DrawTime": draw_time,
                    "Digit1": d1,
                    "Digit2": d2,
                    "Digit3": d3,
                })
            except Exception:
                continue
    if not draws:
        return pd.DataFrame()
    df = pd.DataFrame(draws)
    df["Digit1"] = df["Digit1"].astype(int)
    df["Digit2"] = df["Digit2"].astype(int)
    df["Digit3"] = df["Digit3"].astype(int)
    df["DrawKey"] = df["Date"].dt.strftime("%Y-%m-%d") + "_" + df["DrawTime"]
    return df


def load_history() -> pd.DataFrame:
    if HISTORY_CSV.exists():
        df = pd.read_csv(HISTORY_CSV, parse_dates=["Date"])
        # ensure types
        for col in ["Digit1", "Digit2", "Digit3"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        if "DrawTime" not in df:
            df["DrawTime"] = ""
        if "DrawKey" not in df:
            df["DrawKey"] = df["Date"].dt.strftime("%Y-%m-%d") + "_" + df["DrawTime"].astype(str)
        return df
    else:
        return pd.DataFrame(columns=["Date", "DrawTime", "Digit1", "Digit2", "Digit3", "DrawKey"])


def merge_and_dedupe(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if new.empty:
        logger.info("No new data to merge.")
        return existing
    combined = pd.concat([existing, new], ignore_index=True)
    combined = combined.drop_duplicates(subset=["DrawKey"], keep="last")
    # Sort descending by date/time
    combined = combined.sort_values(["Date", "DrawTime"], ascending=[False, True])
    # Recompute DrawKey if missing
    combined["DrawKey"] = combined["Date"].dt.strftime("%Y-%m-%d") + "_" + combined["DrawTime"].astype(str)
    return combined.reset_index(drop=True)


def make_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"error": "no data"}
    latest = df.iloc[0]
    summary = {
        "latest": {
            "Date": latest["Date"].strftime("%Y-%m-%d") if not pd.isna(latest["Date"]) else None,
            "DrawTime": str(latest.get("DrawTime", "")),
            "Digits": [int(latest["Digit1"]), int(latest["Digit2"]), int(latest["Digit3"])],
        },
        "total_draws": int(len(df)),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        # potential place to add frequencies, patterns etc.
    }
    return summary


def json_safe(obj):
    """Recursively convert numpy/int64/etc to native Python."""
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_safe(v) for v in obj]
    elif hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except Exception:
            pass
    return obj


def main():
    logger.info("Running prepare_data at %s UTC", datetime.now(timezone.utc).isoformat())

    # Step 1: Acquire PDF (best-effort)
    fetched = False
    if not LOCAL_PDF.exists() or os.environ.get("FORCE_REFRESH", "false").lower() == "true":
        fetched = download_pdf(LOCAL_PDF)
    else:
        logger.info("Using existing local PDF %s", LOCAL_PDF)

    # Step 2: Parse source
    parsed_df = pd.DataFrame()
    if fetched or LOCAL_PDF.exists():
        try:
            parsed_df = parse_pdf(LOCAL_PDF)
            logger.info("Parsed %d draws from PDF", len(parsed_df))
        except Exception as e:
            logger.error("Error parsing PDF: %s", e)
    if parsed_df.empty and LOCAL_HTML.exists():
        logger.info("Falling back to HTML parse from %s", LOCAL_HTML)
        parsed_df = parse_html_fallback(LOCAL_HTML)
        if not parsed_df.empty:
            logger.info("Parsed %d draws from HTML fallback", len(parsed_df))

    # Step 3: Merge with history and persist
    history_df = load_history()
    merged_df = merge_and_dedupe(history_df, parsed_df)
    if not merged_df.empty:
        merged_df.to_csv(HISTORY_CSV, index=False)
        logger.info("Wrote merged history with %d total draws to %s", len(merged_df), HISTORY_CSV)
    else:
        logger.warning("Merged dataframe is empty; not overwriting history.")

    # Step 4: Summary
    summary = make_summary(merged_df)
    safe_summary = json_safe(summary)
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(safe_summary, f, indent=2)
    logger.info("Summary written to %s", SUMMARY_JSON)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("prepare_data failed: %s", e)
        sys.exit(1)
