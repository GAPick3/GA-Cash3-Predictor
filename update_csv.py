import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import os
import sys
from zoneinfo import ZoneInfo

CSV_PATH = "data/ga_cash3_history.csv"

# Scheduled draw times in Georgia (Eastern) local time
DRAW_SCHEDULE = {
    "Midday": time(12, 20),   # 12:20 PM ET
    "Evening": time(18, 59),  # 6:59 PM ET
    "Night": time(23, 34),    # 11:34 PM ET
}

EASTERN = ZoneInfo("America/New_York")  # Georgia is Eastern Time

def fetch_latest_results():
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    session = requests.Session()
    session.headers.update(headers)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔎 Fetching draw page (attempt {attempt}): {url}")
            r = session.get(url, timeout=10)
            if r.status_code == 403:
                raise requests.exceptions.HTTPError(f"403 Forbidden")
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"⚠️ Fetch attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"   retrying after {wait}s...")
                import time as _t
                _t.sleep(wait)
            else:
                print("❌ All fetch attempts failed.")
                return None

def parse_draws(page_html):
    if not page_html:
        return []

    soup = BeautifulSoup(page_html, "html.parser")
    rows = soup.select("table.results tbody tr")
    parsed = []

    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            date_str = cols[0].text.strip()
            draw_label = cols[1].text.strip()
            number_text = cols[2].text.strip()

            # normalize draw label to match keys (capitalized)
            draw_label = draw_label.title()
            if draw_label not in DRAW_SCHEDULE:
                continue

            # parse date
            draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()

            # parse numbers: expect three digits
            numbers = [n for n in number_text.split() if n.isdigit()]
            if len(numbers) != 3:
                continue

            parsed.append({
                "Date": draw_date,
                "Draw": draw_label,
                "Digit1": int(numbers[0]),
                "Digit2": int(numbers[1]),
                "Digit3": int(numbers[2]),
            })
        except Exception as e:
            print(f"⚠️ Skipping a row due to parse error: {e}")
            continue
    return parsed

def is_time_to_add(draw_date, draw_label):
    """Return True if current UTC is at least 30 minutes after that draw's scheduled time."""
    scheduled_time = DRAW_SCHEDULE.get(draw_label)
    if not scheduled_time:
        return False
    # Build localized datetime for the draw
    local_dt = datetime.combine(draw_date, scheduled_time).replace(tzinfo=EASTERN)
    allowed_dt = local_dt + timedelta(minutes=30)  # wait 30 minutes after draw
    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    return now_utc >= allowed_dt.astimezone(ZoneInfo("UTC"))

def append_new_draws():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_PATH):
        df_existing = pd.read_csv(CSV_PATH, parse_dates=["Date"])
        df_existing.rename(columns=lambda c: c.strip(), inplace=True)
    else:
        df_existing = pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

    existing_keys = set(
        df_existing[["Date", "Draw"]]
        .dropna()
        .apply(lambda r: (pd.to_datetime(r["Date"]).date(), r["Draw"]), axis=1)
        .tolist()
    )

    html = fetch_latest_results()
    new_parsed = parse_draws(html)
    if not new_parsed:
        print("ℹ️ No parsed draws available (maybe fetch failed).")
        return

    added = 0
    for entry in new_parsed:
        key = (entry["Date"], entry["Draw"])
        if key in existing_keys:
            continue  # already have it

        if not is_time_to_add(entry["Date"], entry["Draw"]):
            print(f"⏳ Too early to add draw {entry['Draw']} on {entry['Date']}, waiting until 30m after scheduled time.")
            continue

        # attach DrawTime string
        scheduled_time = DRAW_SCHEDULE[entry["Draw"]]
        # format like "12:20 PM"
        draw_time_str = datetime.combine(entry["Date"], scheduled_time).strftime("%-I:%M %p")
        row = {
            "Date": entry["Date"].isoformat(),
            "Draw": entry["Draw"],
            "DrawTime": draw_time_str,
            "Digit1": entry["Digit1"],
            "Digit2": entry["Digit2"],
            "Digit3": entry["Digit3"],
        }
        # prepend newest
        df_existing = pd.concat([pd.DataFrame([row]), df_existing], ignore_index=True)
        added += 1

    if added:
        # sort newest first
        if "Date" in df_existing.columns:
            df_existing["Date"] = pd.to_datetime(df_existing["Date"])
            df_existing.sort_values(["Date", "Draw"], ascending=[False, True], inplace=True)
        df_existing.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s) to {CSV_PATH}")
    else:
        print("✅ No new draws to add. File is up to date.")

if __name__ == "__main__":
    append_new_draws()
