import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

CSV_PATH = "data/ga_cash3_history.csv"

# Known draw times
DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

# Custom order for sorting Draw times
DRAW_ORDER = {"Midday": 1, "Evening": 2, "Night": 3}

def fetch_latest_results():
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"🔎 Fetching: {url}")
    
    try:
        resp = requests.get(url, headers=headers)
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

            draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            numbers = [int(n) for n in number_text.split() if n.isdigit()]

            if len(numbers) == 3 and draw_label in DRAW_TIMES:
                new_rows.append({
                    "Date": draw_date.isoformat(),
                    "Draw": draw_label,
                    "DrawTime": DRAW_TIMES[draw_label],
                    "Digit1": numbers[0],
                    "Digit2": numbers[1],
                    "Digit3": numbers[2],
                })
        except Exception as e:
            print(f"⚠️ Skipping row due to error: {e}")
            continue

    return new_rows


def append_new_draws():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

    existing_keys = set(df[["Date", "Draw"]].apply(tuple, axis=1))

    new_data = fetch_latest_results()
    if not new_data:
        print("ℹ️ No new results found.")
        return

    added = 0
    for row in new_data:
        key = (row["Date"], row["Draw"])
        if key not in existing_keys:
            df = pd.concat([pd.DataFrame([row]), df], ignore_index=True)
            added += 1

    if added > 0:
        df["DrawSort"] = df["Draw"].map(DRAW_ORDER)
        df.sort_values(by=["Date", "DrawSort"], ascending=[False, True], inplace=True)
        df.drop(columns=["DrawSort"], inplace=True)
        df = df[["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"]]
        df.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s) to {CSV_PATH}")
    else:
        print("✅ No new draws to add. File is up to date.")


if __name__ == "__main__":
    append_new_draws()
