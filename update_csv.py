import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import time
import pdfplumber
import smtplib
from email.message import EmailMessage

CSV_PATH = "data/ga_cash3_history.csv"
PDF_FALLBACK = "data/latest.pdf"  # ensure this exists in repo as a copy of the official PDF

# Known draw times (Eastern Time)
DRAW_TIMES = {
    "Midday": "12:20 PM",
    "Evening": "6:59 PM",
    "Night": "11:34 PM"
}

WEB_URL = "https://www.lotterypost.com/results/georgia/cash-3"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)"
    " Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/115.0.0.0 Safari/537.36",
]

MAX_WEB_ATTEMPTS = 3
BACKOFF_BASE = 2  # exponential backoff multiplier


def fetch_from_web():
    headers = {"User-Agent": USER_AGENTS[0]}
    for attempt in range(1, MAX_WEB_ATTEMPTS + 1):
        headers["User-Agent"] = USER_AGENTS[(attempt - 1) % len(USER_AGENTS)]
        print(f"🔎 Fetching draw page (attempt {attempt}): {WEB_URL} with UA={headers['User-Agent']}")
        try:
            resp = requests.get(WEB_URL, headers=headers, timeout=10)
            if resp.status_code == 403:
                raise requests.HTTPError(f"{resp.status_code} Forbidden")
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
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

                    draw_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                    numbers = [int(n) for n in number_text.split() if n.isdigit()]
                    if len(numbers) != 3:
                        continue
                    if draw_label not in DRAW_TIMES:
                        continue
                    full_time = DRAW_TIMES[draw_label]
                    parsed.append({
                        "Date": draw_date.isoformat(),
                        "Draw": draw_label,
                        "DrawTime": full_time,
                        "Digit1": numbers[0],
                        "Digit2": numbers[1],
                        "Digit3": numbers[2],
                    })
                except Exception as e:
                    print(f"⚠️ row parse skip: {e}")
            if parsed:
                return parsed
            else:
                print("ℹ️ Web fetch succeeded but no valid rows parsed.")
                return []
        except Exception as e:
            print(f"⚠️ Fetch attempt {attempt} failed: {e}")
            if attempt < MAX_WEB_ATTEMPTS:
                sleep = BACKOFF_BASE ** attempt
                print(f"   retrying after {sleep}s...")
                time.sleep(sleep)
    print("❌ All web fetch attempts failed.")
    return None  # signal failure to trigger fallback


def fetch_from_pdf():
    if not os.path.exists(PDF_FALLBACK):
        print(f"❌ PDF fallback missing: {PDF_FALLBACK}")
        return []

    print(f"📄 Falling back to PDF parsing ({PDF_FALLBACK})")
    parsed = []
    try:
        with pdfplumber.open(PDF_FALLBACK) as pdf:
            # assuming all data on first page
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                headers = [h.strip() for h in table[0]]
                # Expect header like: Date, Draw, Winning Numbers, ...
                for row in table[1:]:
                    try:
                        row_dict = dict(zip(headers, row))
                        date_raw = row_dict.get("Date", "").strip()
                        draw_label = row_dict.get("Draw", "").strip()
                        winning = row_dict.get("Winning Numbers", "").strip()
                        if not date_raw or not draw_label or not winning:
                            continue
                        # parse date in MM/DD/YYYY or other (from sample appears MM/DD/YYYY)
                        draw_date = datetime.strptime(date_raw, "%m/%d/%Y").date()
                        numbers = [int(n) for n in winning.split() if n.isdigit()]
                        if len(numbers) != 3:
                            continue
                        if draw_label not in DRAW_TIMES:
                            # sometimes PDF uses lowercase or different casing
                            normalized = draw_label.title()
                        else:
                            normalized = draw_label
                        full_time = DRAW_TIMES.get(normalized, "")
                        parsed.append({
                            "Date": draw_date.isoformat(),
                            "Draw": normalized,
                            "DrawTime": full_time,
                            "Digit1": numbers[0],
                            "Digit2": numbers[1],
                            "Digit3": numbers[2],
                        })
                    except Exception as e:
                        print(f"⚠️ PDF row skip: {e}")
    except Exception as e:
        print(f"❌ Error opening/parsing PDF: {e}")
    return parsed


def load_existing_df():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])


def merge_and_save(new_rows):
    df = load_existing_df()
    existing = set(df[["Date", "Draw"]].apply(tuple, axis=1))
    added = 0
    for row in new_rows:
        key = (row["Date"], row["Draw"])
        if key not in existing:
            df = pd.concat([pd.DataFrame([row]), df], ignore_index=True)
            added += 1
    if added:
        df.sort_values(by=["Date", "Draw"], ascending=[False, False], inplace=True)
        df.to_csv(CSV_PATH, index=False)
    return added, df


def send_email(subject: str, body: str):
    # optional: configure via env vars
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("EMAIL_TO")
    if not all([smtp_server, smtp_user, smtp_password, recipient]):
        print("ℹ️ Email not sent: incomplete SMTP/recipient configuration.")
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg.set_content(body)

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        print("📧 Notification email sent.")
    except Exception as e:
        print(f"❌ Email send failed: {e}")


def main():
    new_rows = fetch_from_web()
    if new_rows is None:  # web failed
        new_rows = fetch_from_pdf()

    if not new_rows:
        print("ℹ️ No new draws fetched from any source.")
        return

    added, df = merge_and_save(new_rows)
    if added:
        msg = f"✅ Added {added} new draw(s). Latest draw: {df.iloc[0].to_dict()}"
    else:
        msg = "✅ No new draws to add; CSV is up to date."
    print(msg)

    # optional email
    send_email("GA Cash3 CSV Update", msg)


if __name__ == "__main__":
    main()
