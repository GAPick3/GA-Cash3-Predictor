import argparse
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone

def parse_args():
    parser = argparse.ArgumentParser(description="Prepare GA Cash3 data from a local PDF.")
    parser.add_argument(
        "--input",
        default="data/latest.pdf",
        help="Path to the uploaded PDF to parse (must exist)."
    )
    return parser.parse_args()

def make_json_serializable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")

def main():
    args = parse_args()
    pdf_path = args.input

    if not os.path.exists(pdf_path):
        logging.error("Input file not found at %s. Upload latest.pdf to that path.", pdf_path)
        sys.exit(1)

    logging.info("Using provided local file %s (no network fetch).", pdf_path)

    # Replace this with your existing PDF parsing logic that returns a DataFrame
    new_draws_df = parse_pdf_to_dataframe(pdf_path)  # you must have this function

    history_path = "data/ga_cash3_history.csv"
    if os.path.exists(history_path):
        existing_df = pd.read_csv(history_path)
    else:
        existing_df = pd.DataFrame()

    # Merge and dedupe
    combined = pd.concat([existing_df, new_draws_df], ignore_index=True)
    combined.drop_duplicates(subset=["Date", "Draw", "Digit1", "Digit2", "Digit3"], inplace=True)
    combined.sort_values(by=["Date", "Draw"], inplace=True)

    # Coerce types if needed (e.g., ensure digits are ints)
    for col in ["Digit1", "Digit2", "Digit3"]:
        if col in combined:
            combined[col] = combined[col].fillna(0).astype(int)

    combined.to_csv(history_path, index=False)
    logging.info("Wrote merged history with %d total draws to %s", len(combined), history_path)

    # Build summary (example fields; adapt to your real summary logic)
    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_draws": int(len(combined)),
        # add any other computed metrics here; make sure values are JSON-serializable or rely on default handler
    }

    with open("data/summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=make_json_serializable)
    logging.info("Summary written to data/summary.json")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
