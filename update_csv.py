#!/usr/bin/env python3
import os
import time
from datetime import datetime, time as dtime, timedelta
import zoneinfo
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Import cleaning logic from prepare_data.py (assumes it's in same package)
from prepare_data import clean, load_raw  # you can adjust if module path differs

CSV_CLEAN = "data/ga_cash3_history.csv"
CSV_RAW = "data/ga_cash3_history_raw.csv"
PDF_FALLBACK = "data/latest.pdf"  # local fallback

# Draw schedule in America/New_York
DRAW_SCHEDULE = {
    "Midday": dtime(12, 20),
    "Evening": dtime(18, 59),
    "Night": dtime(23, 34),
}
# Wait 30 minutes after draw before updating
GRACE = timedelta(minutes=30)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]

def now_et() -> datetime:
    return datetime.now(zoneinfo.ZoneInfo("America/New_York"))

def get_most_recent_due_draw(now: datetime) -> tuple[str, datetime] | None:
    """
    Returns (draw_label, draw_datetime) if we're past draw + GRACE and that draw
    should be fetched now. Otherwise None.
    """
    for label, draw_time in sorted(DRAW_SCHEDULE.items(), key=lambda x: x[1]):
        scheduled = datetime.combine(now.date(), draw_time, tzinfo=zoneinfo.ZoneInfo("America/New_York"))
        # if current time is before the draw on same day, skip to previous day for Night
        if label == "Night" and now.time() < draw_time:
            scheduled = scheduled - timedelta(days=1)
        # If we're >= scheduled + GRACE and < next draw's grace window
        if now >= scheduled + GRACE:
            # Among possible candidates, pick the most recent one satisfying the window
            return label, scheduled
    return None

def scrape_html() -> list[dict]:
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    print(f"🔎 Attempting HTML scrape from {url}")
    last_exception = None
    for idx, ua in enumerate(USER_AGENTS, start=1):
        headers = {"User-Agent": ua}
        backoff = 2 ** (idx - 1)
        try:
            print(f"  Attempt {idx} with UA={ua}")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("table.results tbody tr")
                parsed = []
                for row in rows:
                    try:
                        cols = row.find_all("td")
                        if len(cols) < 3:
                            continue
                        date_str = cols[0].text.strip()
                        draw_label_raw = cols[1].text.strip()
                        number_text = cols[2].text.strip()
                        # Normalize draw label
                        draw_label = None
                        low = draw_label_raw.lower()
                        if "mid" in low:
                            draw_label = "Midday"
                        elif "even" in low:
                            draw_label = "Evening"
                        elif "night" in low:
                            draw_label = "Night"
                        if not draw_label:
                            continue
                        # Parse date
                        draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                        numbers = [int(n) for n in number_text.split() if n.isdigit()]
                        if len(numbers) != 3:
                            continue
                        parsed.append({
                            "Date": draw_date.isoformat(),
                            "Draw": draw_label,
                            "DrawTime": "",  # will be filled by prepare_data
                            "Digit1": numbers[0],
                            "Digit2": numbers[1],
                            "Digit3": numbers[2],
                        })
                    except Exception as e_row:
                        print(f"    skipping row due to parse error: {e_row}")
                if parsed:
                    return parsed
                else:
                    print("    scraped page but found no usable rows.")
            else:
                print(f"    Received status {resp.status_code}, backing off {backoff}s")
                last_exception = Exception(f"HTTP {resp.status_code}")
        except Exception as e:
            last_exception = e
            print(f"    Fetch attempt {idx} failed: {e}; retrying after {backoff}s")
            time.sleep(backoff)
    print("❌ HTML scraping failed entirely.")
    if last_exception:
        print(f"  Last error: {last_exception}")
    return []

def fallback_to_pdf() -> list[dict]:
    if not os.path.exists(PDF_FALLBACK):
        print(f"⚠️ PDF fallback file {PDF_FALLBACK} not present.")
        return []
    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber not installed; cannot parse PDF fallback.")
        return []

    print(f"📄 Parsing fallback PDF at {PDF_FALLBACK}")
    draws = []
    try:
        with pdfplumber.open(PDF_FALLBACK) as pdf:
            # naive: take last page, extract text lines; adapt if format known
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            # Example assumes lines like "07/25/2025 Night 3 7 7 808" etc.;
            # You must adapt parsing to the actual PDF layout.
            for line in text.splitlines():
                parts = line.strip().split()
                # crude check: date at start MM/DD/YYYY, then draw label, then three digits
                if len(parts) >= 6:
                    date_part = parts[0]
                    draw_label_raw = parts[1]
                    # after that somewhere three digits triplet; assume next three are digits
                    digit_candidates = []
                    for tok in parts[2:5]:
                        if tok.isdigit() and len(tok) == 1:
                            digit_candidates.append(int(tok))
                    if len(digit_candidates) != 3:
                        continue
                    try:
                        draw_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                    except Exception:
                        continue
                    label = draw_label_raw.capitalize()
                    if label not in ["Midday", "Evening", "Night"]:
                        continue
                    draws.append({
                        "Date": draw_date.isoformat(),
                        "Draw": label,
                        "DrawTime": "",  # to be filled later
                        "Digit1": digit_candidates[0],
                        "Digit2": digit_candidates[1],
                        "Digit3": digit_candidates[2],
                    })
    except Exception as e:
        print(f"  PDF parse error: {e}")
    return draws

def load_existing_cleaned() -> pd.DataFrame:
    if os.path.exists(CSV_CLEAN):
        return pd.read_csv(CSV_CLEAN, dtype=str)
    return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

def already_has_draw(existing_df: pd.DataFrame, target_draw: str, target_date: datetime) -> bool:
    subset = existing_df[
        (existing_df["Draw"] == target_draw) & (existing_df["Date"] == target_date.date().isoformat())
    ]
    return not subset.empty

def main():
    now_local = now_et()
    due = get_most_recent_due_draw(now_local)
    if not due:
        print(f"ℹ️ No draw is due yet for update (current ET: {now_local.strftime('%Y-%m-%d %H:%M')}). Exiting.")
        return
    draw_label, scheduled_dt = due
    print(f"🕒 Evaluating update for draw '{draw_label}' scheduled at {scheduled_dt.strftime('%Y-%m-%d %H:%M %Z')} (ET)")

    cleaned_df = load_existing_cleaned()
    if already_has_draw(cleaned_df, draw_label, scheduled_dt):
        print(f"✅ Draw {draw_label} on {scheduled_dt.date().isoformat()} already present. Skipping fetch.")
        return

    # Fetch new raw rows
    new_rows = scrape_html()
    if not new_rows:
        new_rows = fallback_to_pdf()

    if not new_rows:
        print("⚠️ No new data fetched from any source. Aborting.")
        return

    # Append to raw history file for audit (optional)
    raw_df = pd.DataFrame(new_rows)
    if os.path.exists(CSV_RAW):
        try:
            existing_raw = pd.read_csv(CSV_RAW, dtype=str)
            raw_df = pd.concat([raw_df, existing_raw], ignore_index=True)
        except Exception:
            pass
    os.makedirs(os.path.dirname(CSV_RAW), exist_ok=True)
    raw_df.to_csv(CSV_RAW, index=False)

    # Now clean/normalize using prepare_data.clean
    cleaned_candidate = clean(raw_df)

    # Merge with existing cleaned, deduplicate, prefer newest (clean() already sorts)
    combined = pd.concat([cleaned_candidate, cleaned_df], ignore_index=True)
    final = combined.drop_duplicates(subset=["Date", "Draw"], keep="first")
    # Ensure sorting same as clean expects: use prepare_data logic by re-running clean on combined raw if desired
    final = final.sort_values(by=["Date", "Draw"], ascending=[False, True])  # simple fallback

    # Write back
    os.makedirs(os.path.dirname(CSV_CLEAN), exist_ok=True)
    final.to_csv(CSV_CLEAN, index=False)
    print(f"✅ Updated cleaned CSV written to {CSV_CLEAN}")

if __name__ == "__main__":
    main()
