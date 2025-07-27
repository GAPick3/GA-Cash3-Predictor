import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import os

def fetch_data():
    url = "https://www.lotterypost.com/results/ga/cash3/past"
    print(f"🔎 Scraping: {url}")

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    today = datetime.now().date()
    three_years_ago = today - timedelta(days=3 * 365)

    data = []

    # This part is hypothetical — we’ll fine-tune once we inspect the real page
    rows = soup.select("table.results-table tbody tr")

    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            date_str = cols[0].text.strip()
            date = datetime.strptime(date_str, "%m/%d/%Y").date()

            if date < three_years_ago:
                continue

            draw_time = cols[1].text.strip().lower()  # Could be 'midday', 'evening', etc.
            numbers = cols[2].text.strip().replace("–", "").replace(" ", "")
            digits = list(numbers)

            if len(digits) == 3 and all(d.isdigit() for d in digits):
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
