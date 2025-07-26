# scraper.py
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URLS = {
    "Midday": "https://www.lotteryusa.com/georgia/midday-3/year",
    "Evening": "https://www.lotteryusa.com/georgia/evening-3/year",
    "Night": "https://www.lotteryusa.com/georgia/night-3/year"
}

OUTFILE = "data/ga_cash3_history.csv"

def scrape_url(draw_type, url):
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table", {"class": "archive-table"})
    rows = table.find_all("tr")[1:]  # skip header
    records = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        date_str = cols[0].text.strip()
        numbers = cols[1].text.strip().split("–")  # en-dash
        if len(numbers) != 3:
            continue
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y").date()
            d1, d2, d3 = [int(n.strip()) for n in numbers]
            records.append((dt.isoformat(), draw_type, d1, d2, d3))
        except Exception:
            continue

    return records

def gather_all():
    all_records = []
    for draw_type, url in URLS.items():
        print(f"📥 Gathering {draw_type} draws...")
        recs = scrape_url(draw_type, url)
        all_records.extend(recs)
    return all_records

def save_csv(records):
    seen = set()
    rows = []
    for rec in records:
        if rec in seen:
            continue
        seen.add(rec)
        rows.append(rec)
    rows.sort()
    with open(OUTFILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Type", "D1", "D2", "D3"])
        writer.writerows(rows)
    print(f"✅ Wrote {len(rows)} records to {OUTFILE}")

if __name__ == "__main__":
    all_data = gather_all()
    save_csv(all_data)
