#!/usr/bin/env python3
import argparse
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
import re

import pandas as pd
import pdfplumber

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HISTORY_PATH = Path("data/ga_cash3_history.csv")
SUMMARY_PATH = Path("data/summary.json")


def extract_digits_from_row(row):
    """
    Try to pull three digits from a PDF table row.
    Supports:
      - Separate columns for Digit1, Digit2, Digit3
      - Combined "7 7 1" or "7,7,1" in one column
    Returns tuple (d1, d2, d3) or None if cannot.
    """
    # Try separate columns first: look for three int-like cells in a row
    for i in range(len(row) - 2):
        slice_ = row[i : i + 3]
        try:
            digits = [int(re.sub(r"\D", "", str(c))) for c in slice_]
            if all(0 <= d <= 9 for d in digits):
                return digits
        except Exception:
            continue

    # Fallback: look for a cell with three numbers together
    for cell in row:
        if not cell:
            continue
        cleaned = cell.replace(",", " ").strip()
        parts = cleaned.split()
        if len(parts) == 3:
            try:
                digits = [int(p) for p in parts]
                if all(0 <= d <= 9 for d in digits):
                    return digits
            except ValueError:
                continue
    return None


def parse_pdf_to_dataframe(pdf_path: Path) -> pd.DataFrame:
    """
    Parses the provided PDF and returns a DataFrame with columns:
    Date, Draw, Digit1, Digit2, Digit3
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    logger.info(f"Parsing PDF at {pdf_path}")
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for raw in table:
                    if not raw or len(raw) < 2:
                        continue

                    # Skip header-like rows
                    joined = " ".join([str(c).lower() if c else "" for c in raw])
                    if "date" in joined and "draw" in joined:
                        continue

                    # Attempt to find draw type ("Midday", "Evening", "Night")
                    draw_cell = None
                    for cell in raw:
                        if not cell:
                            continue
                        if isinstance(cell, str) and cell.strip().lower() in ("midday", "evening", "night"):
                            draw_cell = cell.strip().title()
                            break
                    if not draw_cell:
                        # maybe it's second column if consistent
                        candidate = raw[1] if len(raw) > 1 else ""
                        if isinstance(candidate, str) and candidate.strip().lower() in ("midday", "evening", "night"):
                            draw_cell = candidate.strip().title()
                    if not draw_cell:
                        continue  # cannot determine draw type

                    # Date: look for anything matching MM/DD/YYYY or similar in the row
                    date_cell = None
                    date_pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
                    for cell in raw:
                        if not cell:
                            continue
                        m = date_pattern.search(cell)
                        if m:
                            try:
                                parsed = datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat()
                                date_cell = parsed
                                break
                            except Exception:
                                date_cell = m.group(1)
                                break
                    if not date_cell:
                        continue  # no date, skip

                    # Extract digits
                    digits = extract_digits_from_row(raw)
                    if not digits:
                        logger.debug("Skipping row; couldn't extract digits: %s", raw)
                        continue
                    d1, d2, d3 = digits

                    rows.append({
                        "Date": date_cell,
                        "Draw": draw_cell,
                        "Digit1": d1,
                        "Digit2": d2,
                        "Digit3": d3,
                    })

    if not rows:
        logger.warning("No valid rows parsed from PDF; returning empty DataFrame.")
    df = pd.DataFrame(rows)
    return df


def compute_simple_insights(df: pd.DataFrame):
    def pick_common_uncommon(series):
        if series.empty:
            return {"common": None, "uncommon": None}
        counts = series.value_counts()
        common = int(counts.idxmax())
        uncommon = int(counts.idxmin())
        return {"common": common, "uncommon": uncommon}

    common = {
        "Digit1": pick_common_uncommon(df["Digit1"])["common"] if "Digit1" in df else None,
        "Digit2": pick_common_uncommon(df["Digit2"])["common"] if "Digit2" in df else None,
        "Digit3": pick_common_uncommon(df["Digit3"])["common"] if "Digit3" in df else None,
    }
    uncommon = {
        "Digit1": pick_common_uncommon(df["Digit1"])["uncommon"] if "Digit1" in df else None,
        "Digit2": pick_common_uncommon(df["Digit2"])["uncommon"] if "Digit2" in df else None,
        "Digit3": pick_common_uncommon(df["Digit3"])["uncommon"] if "Digit3" in df else None,
    }
    return {"common": common, "uncommon": uncommon}


def build_summary(df: pd.DataFrame):
    insights = compute_simple_insights(df)
    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_draws": int(len(df)),
        "latest_draw": {},
        "predictions": insights,
        "simple_insights": insights,
    }

    if not df.empty:
        latest = df.iloc[-1].to_dict()
        for k, v in list(latest.items()):
            if hasattr(v, "item"):
                latest[k] = v.item()
        summary["latest_draw"] = latest

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("✅ Summary written to %s", SUMMARY_PATH)


def merge_and_write_history(new_df: pd.DataFrame):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if HISTORY_PATH.exists():
        try:
            existing = pd.read_csv(HISTORY_PATH)
        except Exception:
            logger.warning("Existing history unreadable; starting fresh.")
            existing = pd.DataFrame()
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["Date", "Draw", "Digit1", "Digit2", "Digit3"])
    else:
        combined = new_df

    for col in ["Digit1", "Digit2", "Digit3"]:
        if col in combined:
            combined[col] = combined[col].fillna(0).astype(int)
    combined.to_csv(HISTORY_PATH, index=False)
    logger.info("✅ Wrote merged history with %s total draws to %s", len(combined), HISTORY_PATH)
    return combined


def main():
    parser = argparse.ArgumentParser(description="Prepare GA Cash3 data from local PDF input.")
    parser.add_argument(
        "--input", "-i", type=str, default="data/latest.pdf",
        help="Path to local PDF (no network fetching)."
    )
    args = parser.parse_args()
    pdf_path = Path(args.input)

    logger.info("Running prepare_data at %s UTC", datetime.now(timezone.utc).isoformat())
    logger.info("Using provided local file %s (no network fetch).", pdf_path)

    try:
        new_draws_df = parse_pdf_to_dataframe(pdf_path)
    except Exception as e:
        logger.error("Failed to parse PDF: %s", e)
        new_draws_df = pd.DataFrame()

    merged = merge_and_write_history(new_draws_df)
    build_summary(merged)


if __name__ == "__main__":
    main()
