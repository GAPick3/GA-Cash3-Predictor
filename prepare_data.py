# prepare_data.py

import os
import re
import json
from datetime import datetime, timedelta
import pandas as pd
import requests
import pdfplumber
from collections import Counter

# CONFIG / CONSTANTS
CSV_PATH = "data/ga_cash3_history.csv"
PDF_PATH = "data/latest.pdf"
SUMMARY_PATH = "data/summary.json"
# Official or mirrored PDF URL (adjust if you host a copy yourself)
PDF_URL = os.environ.get("PDF_URL", "https://www.lotterypost.com/results/georgia/cash-3/download")  # <-- replace with actual working PDF download if needed

DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

DATE_REGEX = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
TRIPLET_REGEX = re.compile(r"\b(\d)\s*(\d)\s*(\d)\b")  # matches three digits possibly separated by spaces
DRAW_LABELS = ["Midday", "Evening", "Night"]


def download_pdf():
    try:
        print(f"Downloading latest PDF from {PDF_URL}")
        resp = requests.get(PDF_URL, timeout=15)
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
                for line in lines:
                    # Attempt to extract the date if present
                    date_match = DATE_REGEX.search(line)
                    if date_match:
                        try:
                            dt = datetime.strptime(date_match.group(1), "%m/%d/%Y").date()
                            current_date = dt.isoformat()
                        except:
                            current_date = None

                    # Look for draw label and triplet in same or adjacent lines
                    for label in DRAW_LABELS:
                        if label.lower() in line.lower():
                            # try to find triplet digits in the line
                            triplet_match = TRIPLET_REGEX.search(line)
                            if triplet_match:
                                d1, d2, d3 = triplet_match.groups()
                                if current_date:
                                    results.append({
                                        "Date": current_date,
                                        "Draw": label,
                                        "DrawTime": DRAW_TIMES[label],
                                        "Digit1": int(d1),
                                        "Digit2": int(d2),
                                        "Digit3": int(d3),
                                    })
                            else:
                                # maybe numbers are on next line(s)
                                # naive peek ahead not implemented for brevity
                                continue
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
    # new empty df
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
        # optional: ensure consistent types
        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce").dt.date.astype(str)
        combined[["Digit1", "Digit2", "Digit3"]] = combined[["Digit1", "Digit2", "Digit3"]].fillna(0).astype(int)
        combined.sort_values(by=["Date", "Draw"], ascending=[False, True], inplace=True)
        combined.drop_duplicates(subset=["Date", "Draw"], keep="first", inplace=True)
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        combined.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s), wrote {CSV_PATH}")
        return combined
    else:
        print("ℹ️ No new draws to add.")
        return df_existing


def build_summary(df: pd.DataFrame):
    if df.empty:
        print("⚠️ Dataframe empty, skipping summary.")
        return {}

    # Triplet column
    df = df.copy()
    df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)

    # Frequency of triplets
    triplet_counts = Counter(df["Triplet"])
    top_triplets = triplet_counts.most_common(10)

    # Digit frequency by position
    digit1_counts = Counter(df["Digit1"])
    digit2_counts = Counter(df["Digit2"])
    digit3_counts = Counter(df["Digit3"])

    # Hot/cold digits overall (sum of positions)
    overall_digit_counts = Counter()
    for i in range(len(df)):
        overall_digit_counts.update([df.at[i, "Digit1"], df.at[i, "Digit2"], df.at[i, "Digit3"]])

    # Last seen per triplet
    last_seen = {}
    for triplet in triplet_counts:
        subset = df[df["Triplet"] == triplet]
        if not subset.empty:
            last_seen[triplet] = subset.iloc[0]["Date"]

    summary = {
        "total_draws": len(df),
        "top_triplets": [{"triplet": t, "count": c, "last_seen": last_seen.get(t)} for t, c in top_triplets],
        "digit_position_counts": {
            "Digit1": dict(digit1_counts),
            "Digit2": dict(digit2_counts),
            "Digit3": dict(digit3_counts),
        },
        "overall_digit_counts": dict(overall_digit_counts),
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }

    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Summary written to {SUMMARY_PATH}")
    return summary


def main():
    # Only attempt update if we're at least 30 minutes past a scheduled draw time for today or yesterday
    now_utc = datetime.utcnow()
    print(f"Running prepare_data at {now_utc.isoformat()} UTC")

    # Download latest PDF (always attempt; could skip if recently fetched)
    _ = download_pdf()

    parsed = parse_pdf()
    merged_df = merge_and_write(parsed)
    # Build derived fields
    if not merged_df.empty:
        # Ensure Triplet column exists
        merged_df["Triplet"] = merged_df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
        build_summary(merged_df)
    else:
        print("⚠️ No data to summarize.")


if __name__ == "__main__":
    main()
