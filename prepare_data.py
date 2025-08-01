#!/usr/bin/env python3
"""
prepare_data.py

Cleans and normalizes raw Georgia Cash 3 history data CSV into a canonical form:
- Parses/normalizes dates
- Splits combined winning numbers into Digit1/2/3
- Normalizes draw labels (Midday / Evening / Night)
- Injects the standard draw times if missing
- Deduplicates by (Date, Draw)
- Sorts (newest date first, within date: Midday, Evening, Night)
- Outputs cleaned CSV
"""
import pandas as pd
import argparse
import os
import re
from datetime import datetime
from collections import Counter

# Standard draw times (Eastern Time)
DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

# For deterministic ordering within a day
DRAW_ORDER = {
    "Midday": 1,
    "Evening": 2,
    "Night": 3
}

# Canonical column names we expect at output
OUTPUT_COLUMNS = ["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"]


def normalize_draw_label(raw: str) -> str | None:
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().lower()
    if "mid" in cleaned:
        return "Midday"
    if "even" in cleaned:
        return "Evening"
    if "night" in cleaned:
        return "Night"
    # fallback: try exact match title case if it's already one of them
    if raw.title() in DRAW_ORDER:
        return raw.title()
    return None  # unrecognized


def split_winning_numbers(row) -> tuple | None:
    # Accept either a column named "Winning Numbers" or a single field of digits/triplet
    # Extract digits; expecting three single-digit numbers (0-9)
    candidates = []
    if "Winning Numbers" in row and pd.notna(row["Winning Numbers"]):
        candidates = re.findall(r"\d", str(row["Winning Numbers"]))
    elif "WinningNumbers" in row and pd.notna(row["WinningNumbers"]):
        candidates = re.findall(r"\d", str(row["WinningNumbers"]))
    elif "Numbers" in row and pd.notna(row["Numbers"]):
        candidates = re.findall(r"\d", str(row["Numbers"]))
    else:
        # maybe already have Digit1/2/3
        return None

    if len(candidates) >= 3:
        try:
            d1, d2, d3 = int(candidates[0]), int(candidates[1]), int(candidates[2])
            return d1, d2, d3
        except ValueError:
            return None
    return None


def parse_date(raw) -> str | None:
    if pd.isna(raw):
        return None
    # try pandas to_datetime with common formats
    try:
        dt = pd.to_datetime(str(raw), errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def load_raw(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file {path} does not exist.")
    df = pd.read_csv(path, dtype=str)  # read everything as string to clean manually
    # strip whitespace from column names
    df.rename(columns=lambda c: c.strip(), inplace=True)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure we have proper Date, Draw, DrawTime, Digit1/2/3

    # Normalize Date
    df["Date"] = df.get("Date", df.get("date", pd.NA))
    df["Date"] = df["Date"].apply(parse_date)
    df = df[df["Date"].notna()]

    # Normalize Draw label
    raw_draw = df.get("Draw", df.get("draw", pd.NA))
    df["Draw"] = raw_draw.apply(lambda r: normalize_draw_label(r) if pd.notna(r) else None)
    df = df[df["Draw"].notna()]

    # Winning numbers -> Digit1/2/3
    # If Digit1 exists but not numeric, attempt to coerce
    if not {"Digit1", "Digit2", "Digit3"}.issubset(df.columns):
        # try to extract from combined fields
        digits_extracted = df.apply(split_winning_numbers, axis=1)
        df["Digit1"] = df["Digit1"] if "Digit1" in df.columns else None
        df["Digit2"] = df["Digit2"] if "Digit2" in df.columns else None
        df["Digit3"] = df["Digit3"] if "Digit3" in df.columns else None

        for idx, trio in digits_extracted.iteritems():
            if trio:
                d1, d2, d3 = trio
                df.at[idx, "Digit1"] = d1
                df.at[idx, "Digit2"] = d2
                df.at[idx, "Digit3"] = d3

    # Coerce digits to integers; drop rows that fail
    def safe_int(x):
        try:
            return int(x)
        except Exception:
            return None

    df["Digit1"] = df["Digit1"].apply(safe_int)
    df["Digit2"] = df["Digit2"].apply(safe_int)
    df["Digit3"] = df["Digit3"].apply(safe_int)
    df = df[df["Digit1"].notna() & df["Digit2"].notna() & df["Digit3"].notna()]

    # DrawTime: if missing or empty, fill from mapping
    df["DrawTime"] = df.get("DrawTime", pd.NA)
    def fill_time(draw, existing):
        if pd.notna(existing) and str(existing).strip():
            return str(existing).strip()
        return DRAW_TIMES.get(draw, "")
    df["DrawTime"] = df.apply(lambda row: fill_time(row["Draw"], row["DrawTime"]), axis=1)

    # Keep only the canonical columns
    cleaned = df[["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"]].copy()

    # Deduplicate: first sort so newest + correct draw order is dominant
    cleaned["DrawOrder"] = cleaned["Draw"].map(DRAW_ORDER).fillna(999).astype(int)
    cleaned["Date_sort"] = pd.to_datetime(cleaned["Date"], errors="coerce")
    cleaned.sort_values(by=["Date_sort", "DrawOrder"], ascending=[False, True], inplace=True)
    cleaned.drop(columns=["DrawOrder", "Date_sort"], inplace=True)

    # Remove duplicates keeping first (newest + preferred order)
    cleaned = cleaned.drop_duplicates(subset=["Date", "Draw"], keep="first")

    # Final sort for output: newest date first, within date midday->evening->night
    cleaned["DrawOrderForSort"] = cleaned["Draw"].map(DRAW_ORDER).fillna(999).astype(int)
    cleaned["Date_sort2"] = pd.to_datetime(cleaned["Date"], errors="coerce")
    cleaned.sort_values(by=["Date_sort2", "DrawOrderForSort"], ascending=[False, True], inplace=True)
    cleaned.drop(columns=["DrawOrderForSort", "Date_sort2"], inplace=True)

    # Reset index
    cleaned.reset_index(drop=True, inplace=True)
    return cleaned


def summary(df: pd.DataFrame):
    print("=== Summary ===")
    print(f"Total rows: {len(df)}")
    cnt = Counter(df["Draw"])
    for draw in ["Midday", "Evening", "Night"]:
        print(f"  {draw}: {cnt.get(draw,0)} entries")
    latest = df.iloc[0]
    print(f"Most recent draw: {latest['Date']} {latest['Draw']} at {latest['DrawTime']} -> {latest['Digit1']} {latest['Digit2']} {latest['Digit3']}")
    # Frequent triplets overall
    triplets = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
    top = Counter(triplets).most_common(3)
    print("Top overall triplets:", [t for t,_ in top])


def write_output(df: pd.DataFrame, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"✅ Cleaned data written to {out_path}")


def parse_args():
    p = argparse.ArgumentParser(description="Clean and normalize GA Cash 3 history CSV.")
    p.add_argument("--input", "-i", default="data/ga_cash3_history.csv", help="Raw input CSV path.")
    p.add_argument("--output", "-o", default="data/ga_cash3_history.csv", help="Cleaned output CSV path.")
    p.add_argument("--inplace", action="store_true", help="Overwrite input instead of writing to output separately.")
    return p.parse_args()


def main():
    args = parse_args()
    input_path = args.input
    output_path = args.output if not args.inplace else input_path

    try:
        raw = load_raw(input_path)
    except Exception as e:
        print(f"❌ Failed to load input CSV: {e}")
        return

    cleaned = clean(raw)
    if cleaned.empty:
        print("⚠️ No valid rows after cleaning; aborting.")
        return

    summary(cleaned)
    write_output(cleaned, output_path)


if __name__ == "__main__":
    main()
