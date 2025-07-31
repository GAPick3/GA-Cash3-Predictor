import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import os
import sys
from zoneinfo import ZoneInfo
import pdfplumber
import re

CSV_PATH = "data/ga_cash3_history.csv"
PDF_FALLBACK_PATH = "data/latest.pdf"  # place the latest GA Cash 3 winning numbers PDF here

# Scheduled draw times in Georgia (Eastern) local time
DRAW_SCHEDULE = {
    "Midday": time(12, 20),   # 12:20 PM ET
    "Evening": time(18, 59),  # 6:59 PM ET
    "Night": time(23, 34),    # 11:34 PM ET
}

EASTERN = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def fetch_latest_results_html():
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
                raise requests.exceptions.HTTPError("403 Forbidden")
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"⚠️ Fetch attempt {attempt} failed: {e}")
            if attempt < max_retries:
                backoff = 2 ** attempt
                print(f"   retrying after {backoff}s...")
                import time as _t
                _t.sleep(backoff)
            else:
                print("❌ All web fetch attempts failed.")
                return None


def parse_draws_from_html(html):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table.results tbody tr")
    parsed = []
    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            date_str = cols[0].text.strip()
            draw_label = cols[1].text.strip().title()
            number_text = cols[2].text.strip()

            if draw_label not in DRAW_SCHEDULE:
                continue

            draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            numbers = [n for n in number_text.split() if n.isdigit()]
            if len(numbers) != 3:
                continue

            parsed.append({
                "Date": draw_date,
                "Draw": draw_label,
                "Digit1": int(numbers[0]),
                "Digit2": int(numbers[1]),
                "Digit3": int(numbers[2]),
                "Source": "web",
            })
        except Exception as e:
            print(f"⚠️ HTML parse row skipped: {e}")
            continue
    return parsed


def parse_draws_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print("⚠️ PDF fallback file not found:", pdf_path)
        return []

    print(f"📄 Falling back to PDF parsing ({pdf_path})")
    parsed = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # This assumes that the PDF contains a table similar to the sample:
            # Date | Draw | Winning Numbers ...
            for page in pdf.pages:
                # Try to extract table data
                tables = page.extract_tables()
                if not tables:
                    # fallback to line-based regex scanning
                    text = page.extract_text() or ""
                    lines = text.splitlines()
                    for line in lines:
                        # Example line: "07/25/2025 Night 3 7 7 808 $126,139"
                        match = re.match(
                            r"(\d{2}/\d{2}/\d{4})\s+(Midday|Evening|Night)\s+([0-9])\s+([0-9])\s+([0-9])",
                            line,
                            re.IGNORECASE,
                        )
                        if match:
                            date_str, draw_label, d1, d2, d3 = match.groups()
                            draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                            draw_label = draw_label.title()
                            if draw_label not in DRAW_SCHEDULE:
                                continue
                            parsed.append({
                                "Date": draw_date,
                                "Draw": draw_label,
                                "Digit1": int(d1),
                                "Digit2": int(d2),
                                "Digit3": int(d3),
                                "Source": "pdf",
                            })
                else:
                    for table in tables:
                        # Heuristic: first row might be headers
                        for row in table[1:]:  # skip header
                            try:
                                if len(row) < 4:
                                    continue
                                date_str = row[0].strip()
                                draw_label = row[1].strip().title()
                                # Winning numbers might be in 3 separate columns or one; attempt both
                                digits = []
                                if row[2] and re.fullmatch(r"\d", row[2].strip()):
                                    digits.append(row[2].strip())
                                if row[3] and re.fullmatch(r"\d", row[3].strip()):
                                    digits.append(row[3].strip())
                                if len(row) >= 5 and row[4] and re.fullmatch(r"\d", row[4].strip()):
                                    digits.append(row[4].strip())
                                if len(digits) != 3:
                                    # maybe they are in a combined cell like "7 8 6"
                                    combined = row[2] or ""
                                    parts = [p for p in combined.split() if p.isdigit()]
                                    if len(parts) == 3:
                                        digits = parts
                                if len(digits) != 3:
                                    continue
                                draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                                if draw_label not in DRAW_SCHEDULE:
                                    continue
                                parsed.append({
                                    "Date": draw_date,
                                    "Draw": draw_label,
                                    "Digit1": int(digits[0]),
                                    "Digit2": int(digits[1]),
                                    "Digit3": int(digits[2]),
                                    "Source": "pdf",
                                })
                            except Exception as e:
                                print(f"⚠️ PDF row parse issue: {e}")
                                continue
    except Exception as e:
        print(f"❌ Error opening/parsing PDF: {e}")
    return parsed


def is_time_to_add(draw_date, draw_label):
    scheduled_time = DRAW_SCHEDULE.get(draw_label)
    if not scheduled_time:
        return False
    local_dt = datetime.combine(draw_date, scheduled_time).replace(tzinfo=EASTERN)
    allowed_dt = local_dt + timedelta(minutes=30)
    now_utc = datetime.now(tz=UTC)
    return now_utc >= allowed_dt.astimezone(UTC)


def append_new_draws():
    os.makedirs("data", exist_ok=True)

    if os.path.exists(CSV_PATH):
        df_existing = pd.read_csv(CSV_PATH, parse_dates=["Date"])
        df_existing.rename(columns=lambda c: c.strip(), inplace=True)
    else:
        df_existing = pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

    # Build existing keys (Date as date, Draw)
    existing_keys = set(
        df_existing[["Date", "Draw"]]
        .dropna()
        .apply(lambda r: (pd.to_datetime(r["Date"]).date(), r["Draw"]), axis=1)
        .tolist()
    )

    # Try web fetch first
    html = fetch_latest_results_html()
    parsed = parse_draws_from_html(html)
    if not parsed:
        # Fallback to PDF
        parsed = parse_draws_from_pdf(PDF_FALLBACK_PATH)

    if not parsed:
        print("ℹ️ No new draw data available from any source.")
        return

    added = 0
    for entry in parsed:
        key = (entry["Date"], entry["Draw"])
        if key in existing_keys:
            continue
        if not is_time_to_add(entry["Date"], entry["Draw"]):
            print(f"⏳ Skipping {entry['Draw']} on {entry['Date']} (too soon; <30m after scheduled).")
            continue

        scheduled_time = DRAW_SCHEDULE[entry["Draw"]]
        draw_time_str = datetime.combine(entry["Date"], scheduled_time).strftime("%-I:%M %p")
        row = {
            "Date": entry["Date"].isoformat(),
            "Draw": entry["Draw"],
            "DrawTime": draw_time_str,
            "Digit1": entry["Digit1"],
            "Digit2": entry["Digit2"],
            "Digit3": entry["Digit3"],
        }
        df_existing = pd.concat([pd.DataFrame([row]), df_existing], ignore_index=True)
        added += 1

    if added:
        if "Date" in df_existing.columns:
            df_existing["Date"] = pd.to_datetime(df_existing["Date"])
            df_existing.sort_values(["Date", "Draw"], ascending=[False, True], inplace=True)
        df_existing.to_csv(CSV_PATH, index=False)
        print(f"✅ Added {added} new draw(s) to {CSV_PATH}")
    else:
        print("✅ No new draws to add. File is up to date.")


if __name__ == "__main__":
    append_new_draws()
