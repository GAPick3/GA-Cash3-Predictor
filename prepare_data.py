import argparse
import os
import sys
import json
import logging
from datetime import datetime, timezone
import re

import pandas as pd
import numpy as np
import pdfplumber

HISTORY_CSV = "data/ga_cash3_history.csv"
SUMMARY_JSON = "data/summary.json"


def make_json_serializable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, datetime):
        return o.isoformat()
    return o  # fallback, should be primitive


def parse_pdf_to_dataframe(pdf_path: str) -> pd.DataFrame:
    """
    Parses the provided GA Cash3 PDF and returns a DataFrame with columns:
    Date, Draw, Digit1, Digit2, Digit3, Winners, Total_payout
    """
    rows = []
    line_pattern = re.compile(
        r"(?P<date>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<draw>Night|Evening|Midday)\s+"
        r"(?P<d1>\d)\s+"
        r"(?P<d2>\d)\s+"
        r"(?P<d3>\d)\s+"
        r"(?P<winners>[\d,]+)\s+"
        r"\$?(?P<payout>[\d,]+)"
    )

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.splitlines():
                # skip header-like lines
                m = line_pattern.search(line)
                if m:
                    try:
                        date_str = m.group("date")
                        draw = m.group("draw")
                        d1 = int(m.group("d1"))
                        d2 = int(m.group("d2"))
                        d3 = int(m.group("d3"))
                        winners = int(m.group("winners").replace(",", ""))
                        payout = m.group("payout").replace(",", "")
                        # store as string with $ in display if needed
                        total_payout = f"${int(payout):,}"
                        rows.append({
                            "Date": date_str,
                            "Draw": draw,
                            "Digit1": d1,
                            "Digit2": d2,
                            "Digit3": d3,
                            "Winners": winners,
                            "Total_payout": total_payout,
                        })
                    except Exception as e:
                        logging.warning("Failed to parse line [%s]: %s", line, e)
                else:
                    # Sometimes the table extraction is slightly misaligned; try to salvage numeric sequences
                    # attempt fuzzy parse if line contains the known draw words
                    if any(keyword in line for keyword in ("Night", "Evening", "Midday")):
                        parts = line.strip().split()
                        # naive fallback: expect at least 8 tokens
                        if len(parts) >= 8:
                            try:
                                date_str = parts[0]
                                draw = parts[1]
                                d1 = int(parts[2])
                                d2 = int(parts[3])
                                d3 = int(parts[4])
                                winners = int(parts[5].replace(",", ""))
                                payout_raw = parts[6]
                                # strip $ and commas
                                payout_num = int(payout_raw.replace("$", "").replace(",", ""))
                                total_payout = f"${payout_num:,}"
                                rows.append({
                                    "Date": date_str,
                                    "Draw": draw,
                                    "Digit1": d1,
                                    "Digit2": d2,
                                    "Digit3": d3,
                                    "Winners": winners,
                                    "Total_payout": total_payout,
                                })
                            except Exception:
                                pass  # give up on that line

    if not rows:
        logging.warning("No rows parsed from PDF %s; returning empty DataFrame.", pdf_path)
        return pd.DataFrame(
            columns=["Date", "Draw", "Digit1", "Digit2", "Digit3", "Winners", "Total_payout"]
        )

    df = pd.DataFrame(rows)

    # Normalize Date to ISO-like or keep original; here we keep MM/DD/YYYY as string but we could convert
    # Optionally convert to datetime for sorting
    try:
        df["Date_parsed"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    except Exception:
        df["Date_parsed"] = pd.NaT

    # Sort for determinism
    df.sort_values(by=["Date_parsed", "Draw"], inplace=True)
    df.drop(columns=["Date_parsed"], inplace=True, errors=True)

    # Ensure digits are ints
    for col in ["Digit1", "Digit2", "Digit3"]:
        if col in df:
            df[col] = df[col].astype(int)

    # Winners ensure int
    if "Winners" in df:
        df["Winners"] = df["Winners"].astype(int)

    return df


def merge_and_update_history(new_df: pd.DataFrame, history_csv_path: str) -> pd.DataFrame:
    if os.path.exists(history_csv_path):
        existing = pd.read_csv(history_csv_path)
    else:
        existing = pd.DataFrame()

    # If existing is empty, just use new
    if existing.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([existing, new_df], ignore_index=True)

    # Dedupe based on identifying fields
    combined.drop_duplicates(
        subset=["Date", "Draw", "Digit1", "Digit2", "Digit3"],
        inplace=True,
        ignore_index=True,
    )

    # Sort for consistency: try parsing date to sort properly
    combined["Date_parsed"] = pd.to_datetime(combined["Date"], format="%m/%d/%Y", errors="coerce")
    combined.sort_values(by=["Date_parsed", "Draw"], inplace=True)
    combined.drop(columns=["Date_parsed"], inplace=True, errors=True)

    # Ensure types
    for col in ["Digit1", "Digit2", "Digit3"]:
        if col in combined:
            combined[col] = combined[col].fillna(0).astype(int)

    if "Winners" in combined:
        combined["Winners"] = combined["Winners"].fillna(0).astype(int)

    return combined


def compute_simple_insights(df: pd.DataFrame, window=100):
    # Most / least common digits in last `window` draws
    recent = df.sort_values(by=["Date"], ascending=False).head(window)
    insights = {"common": {}, "uncommon": {}}
    for pos in ["Digit1", "Digit2", "Digit3"]:
        if pos in recent:
            counts = recent[pos].value_counts()
            if not counts.empty:
                insights["common"][pos] = int(counts.idxmax())
                insights["uncommon"][pos] = int(counts.idxmin())
            else:
                insights["common"][pos] = None
                insights["uncommon"][pos] = None
    return insights


def build_summary(df: pd.DataFrame) -> dict:
    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_draws": int(len(df)),
        "latest_draw": None,
        "simple_insights": compute_simple_insights(df, window=100),
    }
    if not df.empty:
        latest = df.sort_values(by=["Date"], ascending=False).iloc[0]
        summary["latest_draw"] = {
            "Date": latest.get("Date"),
            "Draw": latest.get("Draw"),
            "Digits": [int(latest.get("Digit1")), int(latest.get("Digit2")), int(latest.get("Digit3"))],
        }
    return summary


def save_summary(summary: dict, path: str):
    with open(path, "w") as f:
        json.dump(summary, f, indent=2, default=make_json_serializable)
    logging.info("Wrote summary to %s", path)


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare and merge GA Cash3 history from a local PDF.")
    parser.add_argument(
        "--input",
        default="data/latest.pdf",
        help="Path to the locally uploaded PDF containing the latest draw data."
    )
    parser.add_argument(
        "--history",
        default=HISTORY_CSV,
        help="Path to the history CSV to read/merge and update."
    )
    parser.add_argument(
        "--summary",
        default=SUMMARY_JSON,
        help="Path to write the summary JSON."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    os.makedirs(os.path.dirname(args.history), exist_ok=True)
    os.makedirs(os.path.dirname(args.summary), exist_ok=True)

    if not os.path.exists(args.input):
        logging.error("Input PDF not found at %s. Please upload the file before running.", args.input)
        sys.exit(1)

    logging.info("Using provided local file %s (no network fetch).", args.input)
    new_draws_df = parse_pdf_to_dataframe(args.input)

    if new_draws_df.empty:
        logging.warning("Parsed PDF produced no new draw rows. Proceeding with existing history (if any).")

    combined_df = merge_and_update_history(new_draws_df, args.history)
    combined_df.to_csv(args.history, index=False)
    logging.info("Wrote merged history with %d total draws to %s", len(combined_df), args.history)

    summary = build_summary(combined_df)
    save_summary(summary, args.summary)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    main()
