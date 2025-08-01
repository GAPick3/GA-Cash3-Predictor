# prepare_data.py
import pandas as pd
import pdfplumber
import os
import json
from datetime import datetime, time, timedelta
from pathlib import Path

CSV_PATH = "data/ga_cash3_history.csv"
PDF_PATH = "data/latest.pdf"
STATUS_PATH = "data/.status.json"

# Fixed draw times in Eastern Time (assume ET; adjust to UTC if needed elsewhere)
DRAW_SCHEDULE = {
    "Midday": {"time": time(12, 20)},   # 12:20 PM
    "Evening": {"time": time(18, 59)},  # 6:59 PM
    "Night": {"time": time(23, 34)}     # 11:34 PM
}
DRAW_TIME_STRINGS = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

def load_status():
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    with open(STATUS_PATH, "w") as f:
        json.dump(status, f)

def parse_pdf():
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found at {PDF_PATH}")
        return []

    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            if not table or len(table) < 2:
                print("⚠️ PDF table missing or malformed.")
                return []

            headers = [h.strip() for h in table[0]]
            rows = []
            for row in table[1:]:
                if len(row) != len(headers):
                    continue
                rowdict = dict(zip(headers, row))
                # Expecting something like Date, Draw, Winning Numbers or similar; adapt if header names differ
                date_raw = rowdict.get("Date", "").strip()
                draw_label = rowdict.get("Draw", "").strip().title()
                numbers = rowdict.get("Winning Numbers", rowdict.get("Winning Number", "")).strip()

                if not date_raw or not draw_label or not numbers:
                    continue

                try:
                    date_parsed = datetime.strptime(date_raw, "%m/%d/%Y").date()
                except ValueError:
                    # try alternate format
                    try:
                        date_parsed = datetime.strptime(date_raw, "%Y-%m-%d").date()
                    except Exception:
                        continue

                digits = [int(n) for n in numbers.split() if n.isdigit()]
                if len(digits) != 3:
                    continue

                if draw_label not in DRAW_TIME_STRINGS:
                    # Normalize variant names (e.g., "Mid Day" -> "Midday")
                    key = draw_label.replace(" ", "").capitalize()
                    if key in DRAW_TIME_STRINGS:
                        draw_label = key
                    else:
                        continue  # unknown draw

                rows.append({
                    "Date": date_parsed.isoformat(),
                    "Draw": draw_label,
                    "DrawTime": DRAW_TIME_STRINGS.get(draw_label, ""),
                    "Digit1": digits[0],
                    "Digit2": digits[1],
                    "Digit3": digits[2]
                })
            return rows
    except Exception as e:
        print("❌ Error parsing PDF:", e)
        return []

def load_existing_df():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

def merge_and_clean(new_rows):
    df = load_existing_df()

    existing_keys = set(df[["Date", "Draw"]].apply(tuple, axis=1))
    added = 0
    for row in new_rows:
        key = (row["Date"], row["Draw"])
        if key not in existing_keys:
            df = pd.concat([pd.DataFrame([row]), df], ignore_index=True)
            added += 1

    if added > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values(by=["Date", "Draw"], ascending=[False, False], inplace=True)
        # Optional: ensure draw-specific ordering (Midday, Evening, Night) if same date
        df["Date"] = df["Date"].dt.date  # keep as date for simplicity
        df.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s) to {CSV_PATH}")
    else:
        print("ℹ️ No new draws to add.")

    return df

def main():
    status = load_status()
    # parse PDF (source of truth)
    new_rows = parse_pdf()
    if new_rows:
        df = merge_and_clean(new_rows)
        status["last_source"] = "pdf"
        status["last_success"] = datetime.utcnow().isoformat() + "Z"
        # set next expected: compute next draw time in ET then +30m (store as ISO UTC for display)
        # skipping complex timezone logic for brevity; front-end can compute expected draw windows if needed
    else:
        print("⚠️ No new rows from PDF; nothing merged.")

    save_status(status)

if __name__ == "__main__":
    main()
