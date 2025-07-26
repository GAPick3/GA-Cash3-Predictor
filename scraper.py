import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import os

def fetch_data(draw_time, year):
    url = f"https://www.lotteryusa.com/georgia/{draw_time}-3/{year}/"
    print(f"🔎 Scraping {draw_time.title()} draws for {year}: {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select(".drawings.table tbody tr")

    data = []
    for row in rows:
        try:
            date_str = row.select_one(".date").text.strip()
            numbers = row.select_one(".result").text.strip().split()
            date = datetime.strptime(date_str, "%m/%d/%Y").date()
            if len(numbers) == 3:
                data.append([date.isoformat(), draw_time] + numbers)
        except Exception as e:
            continue

    return data

def main():
    today = datetime.now().date()
    start_year = (today - timedelta(days=3*365)).year
    end_year = today.year
    all_data = []

    for year in range(start_year, end_year + 1):
        for draw in ['midday', 'evening']:
            all_data.extend(fetch_data(draw, year))

    os.makedirs("data", exist_ok=True)
    with open("data/ga_cash3_history.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Draw", "Number1", "Number2", "Number3"])
        writer.writerows(all_data)

    print(f"✅ Wrote {len(all_data)} records to data/ga_cash3_history.csv")

if __name__ == "__main__":
    main()
