# prepare_data.py

import os
import re
import json
from datetime import datetime, timezone, timedelta
import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup
from collections import Counter

CSV_PATH = "data/ga_cash3_history.csv"
PDF_PATH = "data/latest.pdf"
HTML_FALLBACK = "latest.htm"  # uploaded manually or via pipeline
SUMMARY_PATH = "data/summary.json"
PDF_URL = os.environ.get("PDF_URL", "https://www.lotterypost.com/results/georgia/cash-3/download")

DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}
DRAW_LABELS = list(DRAW_TIMES.keys())
DATE_REGEX = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
TRIPLET_REGEX = re.compile(r"\b(\d)\s*(\d)\s*(\d)\b")


def download_pdf():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
        print("⚠️ PDF not present, skipping PDF parse.")
        return []

    parsed = []
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = text.splitlines()
                current_date = None
                for idx, line in enumerate(lines):
                    # date detection
                    dm = DATE_REGEX.search(line)
                    if dm:
                        try:
                            current_date = datetime.strptime(dm.group(1), "%m/%d/%Y").date().isoformat()
                        except:
                            current_date = None

                    for label in DRAW_LABELS:
                        if label.lower() in line.lower():
                            match = TRIPLET_REGEX.search(line)
                            if not match and idx + 1 < len(lines):
                                match = TRIPLET_REGEX.search(lines[idx + 1])
                            if match and current_date:
                                d1, d2, d3 = match.groups()
                                parsed.append({
                                    "Date": current_date,
                                    "Draw": label,
                                    "DrawTime": DRAW_TIMES[label],
                                    "Digit1": int(d1),
                                    "Digit2": int(d2),
                                    "Digit3": int(d3),
                                })
        print(f"✅ Parsed {len(parsed)} draws from PDF")
    except Exception as e:
        print(f"❌ Error during PDF parsing: {e}")
    return parsed


def parse_html_fallback():
    if not os.path.exists(HTML_FALLBACK):
        print("⚠️ No HTML fallback file; skipping HTML parse.")
        return []

    parsed = []
    try:
        with open(HTML_FALLBACK, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        # This assumes the structure has rows with date, draw label, and numbers.
        table_rows = soup.select("table.results tbody tr")
        for row in table_rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) < 3:
                continue
            date_str = cols[0]
            draw_label = cols[1]
            number_text = cols[2]
            if draw_label not in DRAW_LABELS:
                continue
            try:
                draw_date = datetime.strptime(date_str, "%m/%d/%Y").date().isoformat()
            except:
                continue
            digits = [int(d) for d in re.findall(r"\d", number_text)][:3]
            if len(digits) != 3:
                continue
            parsed.append({
                "Date": draw_date,
                "Draw": draw_label,
                "DrawTime": DRAW_TIMES[draw_label],
                "Digit1": digits[0],
                "Digit2": digits[1],
                "Digit3": digits[2],
            })
        print(f"✅ Parsed {len(parsed)} draws from HTML fallback")
    except Exception as e:
        print(f"❌ HTML fallback parsing failed: {e}")
    return parsed


def load_existing():
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, dtype={"Draw": str})
            return df
        except Exception as e:
            print(f"⚠️ Could not read existing CSV, recreating: {e}")
    return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])


def merge_and_write(new_rows):
    existing = load_existing()
    existing_keys = set(existing[["Date", "Draw"]].apply(tuple, axis=1))
    to_add = []
    for r in new_rows:
        key = (r["Date"], r["Draw"])
        if key not in existing_keys:
            to_add.append(r)

    if to_add:
        df_new = pd.DataFrame(to_add)
        combined = pd.concat([df_new, existing], ignore_index=True)

        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce").dt.date.astype(str)
        for col in ["Digit1", "Digit2", "Digit3"]:
            combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)

        combined["Triplet"] = combined.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
        combined.sort_values(by=["Date", "Draw"], ascending=[False, True], inplace=True)
        combined.drop_duplicates(subset=["Date", "Draw"], keep="first", inplace=True)
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        combined.drop(columns=["Triplet"], errors="ignore").to_csv(CSV_PATH, index=False)
        print(f"✅ Added {len(to_add)} new draw(s), wrote {CSV_PATH}")
        return combined
    else:
        print("ℹ️ No new draws to add.")
        if "Triplet" not in existing.columns:
            existing["Triplet"] = existing.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
        return existing


def sanitize_counter(cnt):
    return {str(k): int(v) for k, v in cnt.items()}


def build_summary(df):
    if df.empty:
        print("⚠️ Empty dataframe; skipping summary.")
        return {}

    df = df.copy()
    df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
    triplet_counts = Counter(df["Triplet"])
    top = triplet_counts.most_common(10)

    digit1 = Counter(df["Digit1"])
    digit2 = Counter(df["Digit2"])
    digit3 = Counter(df["Digit3"])

    overall = Counter()
    for _, row in df.iterrows():
        overall.update([row["Digit1"], row["Digit2"], row["Digit3"]])

    last_seen = {}
    for t in triplet_counts:
        subset = df[df["Triplet"] == t]
        if not subset.empty:
            last_seen[t] = subset.iloc[0]["Date"]

    summary = {
        "total_draws": int(len(df)),
        "top_triplets": [
            {"triplet": t, "count": int(c), "last_seen": last_seen.get(t)}
            for t, c in top
        ],
        "digit_position_counts": {
            "Digit1": sanitize_counter(digit1),
            "Digit2": sanitize_counter(digit2),
            "Digit3": sanitize_counter(digit3),
        },
        "overall_digit_counts": sanitize_counter(overall),
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
    now = datetime.now(timezone.utc)
    print(f"Running prepare_data at {now.isoformat()} UTC")

    _ = download_pdf()  # best effort
    parsed = parse_pdf()

    if not parsed:
        # fallback to HTML if PDF yielded nothing
        parsed = parse_html_fallback()

    merged = merge_and_write(parsed)
    if not merged.empty:
        build_summary(merged)
    else:
        print("⚠️ No data available to summarize.")


if __name__ == "__main__":
    main()
