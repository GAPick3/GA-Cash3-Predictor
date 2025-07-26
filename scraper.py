# scraper.py

import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import os

def fetch_data():
    url = "https://www.lotteryusa.com/georgia/cash-3/"
    print(f"🔎 Scraping: {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table.drawings tbody tr")

    today = datetime.now().date()
    three_years_ago = today - timedelta(days=3*365)

    data = []
    for row in rows:
        try:
            date_cell = row.select_one("td.date")
            if not date_cell:
                continue

            date_str = date_cell.text.strip()
            date = datetime.strptime(date_str, "%A, %B %d, %Y").date()
            if date < three_years_ago:
                continue

            draw_cell = row.select_one("td.draw")
            draw_time = draw_cell.text.strip().lower() if draw_cell else "unknown"

            number_cells = row.select("td.results span")
            digits = [n.text.strip() for n in number_cells if n.text.strip().isdigit()]
            if len(digits) == 3:
                data.append([date.isoformat(), draw_time] + digits)
        except Exception as e:
            continue

    return data

def main():
    all_data = fetch_data()

    os.makedirs("data", exist_ok=True)
    with open("data/ga_cash3_history.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Draw", "Number1", "Number2", "Number3"])
        writer.writerows(all_data)

    print(f"✅ Wrote {len(all_data)} records to data/ga_cash3_history.csv")

if __name__ == "__main__":
    main()
