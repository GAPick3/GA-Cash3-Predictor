import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from zoneinfo import ZoneInfo

CSV_PATH = "data/ga_cash3_history.csv"

# Known draw times in Eastern Time
DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

# Normalize draw label mapping if source uses variations
VALID_DRAWS = set(DRAW_TIMES.keys())

def fetch_latest_results():
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"🔎 Fetching: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print("❌ Error fetching results:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table.results tbody tr")
    new_rows = []

    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            date_str = cols[0].text.strip()
            draw_label = cols[1].text.strip()
            number_text = cols[2].text.strip()

            # Normalize draw label (capitalize)
            draw_label = draw_label.capitalize()
            if draw_label not in VALID_DRAWS:
                continue

            draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()

            # Parse digits
            digits = [int(n) for n in number_text.split() if n.isdigit()]
            if len(digits) != 3:
                continue

            # Attach official draw time
            draw_time = DRAW_TIMES[draw_label]

            new_rows.append({
                "Date": draw_date.isoformat(),
                "Draw": draw_label,
                "DrawTime": draw_time,
                "Digit1": digits[0],
                "Digit2": digits[1],
                "Digit3": digits[2]
            })
        except Exception as e:
            print(f"⚠️ Skipping row due to error: {e}")
            continue

    return new_rows

def append_new_draws():
    if os.path.exists(CSV_PATH):
        df_existing = pd.read_csv(CSV_PATH)
        df_existing.rename(columns=lambda c: c.strip(), inplace=True)
    else:
        df_existing = pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

    existing_keys = set(df_existing[["Date", "Draw"]].apply(tuple, axis=1))
    new_data = fetch_latest_results()
    if not new_data:
        print("ℹ️ No new results fetched.")
        return

    added = 0
    for row in new_data:
        key = (row["Date"], row["Draw"])
        if key not in existing_keys:
            df_existing = pd.concat([pd.DataFrame([row]), df_existing], ignore_index=True)
            added += 1

    if added > 0:
        # Sort newest first
        df_existing["Date"] = pd.to_datetime(df_existing["Date"])
        df_existing.sort_values(["Date", "Draw"], ascending=[False, True], inplace=True)
        # Write back with normalized headers
        df_existing.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s) to {CSV_PATH}")
    else:
        print("✅ No new draws to add. CSV is up to date.")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    append_new_draws()
