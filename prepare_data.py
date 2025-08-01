# prepare_data.py

import os
import re
import json
from datetime import datetime, timezone
import pandas as pd
import requests
import pdfplumber
from collections import Counter
import time

# CONFIG / CONSTANTS
CSV_PATH = "data/ga_cash3_history.csv"
PDF_PATH = "data/latest.pdf"
SUMMARY_PATH = "data/summary.json"
# Replace or override via env if you host a copy yourself:
PDF_URL = os.environ.get("PDF_URL", "https://www.lotterypost.com/results/georgia/cash-3/download")

DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

DATE_REGEX = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
TRIPLET_REGEX = re.compile(r"\b(\d)\s*(\d)\s*(\d)\b")  # three digits potentially spaced
DRAW_LABELS = ["Midday", "Evening", "Night"]


def download_pdf():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        print(f"Downloading latest PDF from {PDF_URL}")
        resp = requests.get(PDF_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)
        with open(PDF_PATH, "wb") as f:
            f.write(resp.content)
        print(f"✅ PDF saved to {PDF_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to download PDF: {e}")
        return False


def parse_pdf():
    if not os.path.exists(PDF_PATH):
        print("❌ PDF not present, skipping parse.")
        return []

    results = []
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = text.splitlines()

                current_date = None
                for i, line in enumerate(lines):
                    # Extract date if present
                    date_match = DATE_REGEX.search(line)
                    if date_match:
                        try:
                            dt = datetime.strptime(date_match.group(1), "%m/%d/%Y").date()
                            current_date = dt.isoformat()
                        except Exception:
                            current_date = None

                    for label in DRAW_LABELS:
                        if label.lower() in line.lower():
                            # Try to find triplet on same line
                            triplet_match = TRIPLET_REGEX.search(line)
                            if not triplet_match and i + 1 < len(lines):
                                # fallback to next line
                                triplet_match = TRIPLET_REGEX.search(lines[i + 1])
                            if triplet_match and current_date:
                                d1, d2, d3 = triplet_match.groups()
                                results.append({
                                    "Date": current_date,
                                    "Draw": label,
                                    "DrawTime": DRAW_TIMES[label],
                                    "Digit1": int(d1),
                                    "Digit2": int(d2),
                                    "Digit3": int(d3),
                                })
        print(f"✅ Parsed {len(results)} draws from PDF")
    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")
    return results


def load_existing():
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, dtype={"Draw": str})
            return df
        except Exception as e:
            print(f"⚠️ Failed to load existing CSV, starting fresh: {e}")
    return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])


def merge_and_write(new_rows):
    df_existing = load_existing()
    existing_keys = set(df_existing[["Date", "Draw"]].apply(tuple, axis=1))

    added = 0
    new_df_rows = []
    for row in new_rows:
        key = (row["Date"], row["Draw"])
        if key not in existing_keys:
            new_df_rows.append(row)
            added += 1

    if added > 0:
        df_new = pd.DataFrame(new_df_rows)
        combined = pd.concat([df_new, df_existing], ignore_index=True)

        # Normalize types
        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce").dt.date.astype(str)
        for col in ["Digit1", "Digit2", "Digit3"]:
            combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)

        # Triplet for internal consistency
        combined["Triplet"] = combined.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)

        combined.sort_values(by=["Date", "Draw"], ascending=[False, True], inplace=True)
        combined.drop_duplicates(subset=["Date", "Draw"], keep="first", inplace=True)
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        combined.drop(columns=["Triplet"], errors="ignore").to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s), wrote {CSV_PATH}")
        return combined
    else:
        print("ℹ️ No new draws to add.")
        # ensure Triplet exists for downstream
        if "Triplet" not in df_existing.columns:
            df_existing["Triplet"] = df_existing.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
        return df_existing


def sanitize_counter(counter_obj):
    """
    Turn Counter with possibly numpy keys/values into plain serializable dict with string keys and int values.
    """
    out = {}
    for k, v in counter_obj.items():
        try:
            key = str(int(k))
        except Exception:
            key = str(k)
        out[key] = int(v)
    return out


def build_summary(df: pd.DataFrame):
    if df.empty:
        print("⚠️ Dataframe empty, skipping summary.")
        return {}

    df = df.copy()
    df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)

    # Frequency of triplets
    triplet_counts = Counter(df["Triplet"])
    top_triplets_raw = triplet_counts.most_common(10)

    # Digit frequency by position
    digit1_counts = Counter(df["Digit1"])
    digit2_counts = Counter(df["Digit2"])
    digit3_counts = Counter(df["Digit3"])

    # Overall digit frequency (all positions)
    overall_digit_counts = Counter()
    for _, row in df.iterrows():
        overall_digit_counts.update([row["Digit1"], row["Digit2"], row["Digit3"]])

    # Last seen per triplet (most recent is first because data is sorted desc)
    last_seen = {}
    for triplet in triplet_counts:
        subset = df[df["Triplet"] == triplet]
        if not subset.empty:
            last_seen[triplet] = subset.iloc[0]["Date"]

    summary = {
        "total_draws": int(len(df)),
        "top_triplets": [
            {
                "triplet": t,
                "count": int(c),
                "last_seen": last_seen.get(t)
            }
            for t, c in top_triplets_raw
        ],
        "digit_position_counts": {
            "Digit1": sanitize_counter(digit1_counts),
            "Digit2": sanitize_counter(digit2_counts),
            "Digit3": sanitize_counter(digit3_counts),
        },
        "overall_digit_counts": sanitize_counter(overall_digit_counts),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    try:
        os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
        with open(SUMMARY_PATH, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Summary written to {SUMMARY_PATH}")
    except Exception as e:
        print(f"❌ Failed to write summary: {e}")
    return summary


def main():
    now_utc = datetime.now(timezone.utc)
    print(f"Running prepare_data at {now_utc.isoformat()} UTC")

    # Try to download latest PDF (best effort)
    downloaded = download_pdf()
    if not downloaded and not os.path.exists(PDF_PATH):
        print("⚠️ No PDF available; continuing with whatever existing CSV content exists.")

    parsed = parse_pdf()
    merged_df = merge_and_write(parsed)

    if not merged_df.empty:
        # Ensure Triplet exists for summary
        if "Triplet" not in merged_df.columns:
            merged_df["Triplet"] = merged_df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
        build_summary(merged_df)
    else:
        print("⚠️ No data to summarize.")


if __name__ == "__main__":
    main()
