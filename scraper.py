import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime, timedelta

BASE_URLS = {
    "Midday": "https://www.lotteryusa.com/georgia/midday-3/{year}/",
    "Evening": "https://www.lotteryusa.com/georgia/evening-3/{year}/",
    "Night": "https://www.lotteryusa.com/georgia/night-3/{year}/"
}

OUTPUT_FILE = "data/ga_cash3_history.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_recent_years(n=3):
    yesterday = datetime.today() - timedelta(days=1)
    return [yesterday.year - i for i in range(n)]

def fetch_year_data(draw_type, base_url, year):
    url = f"{base_url}{year}/"
    print(f"🔎 Scraping {draw_type} draws for {year}: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for row in soup.select("tr.results"):
        cols = row.select("td")
        if len(cols) < 2:
            continue
        date_str = cols[0].get_text(strip=True)
        numbers_str = cols[1].get_text(strip=True)
        numbers = numbers_str.split()
        if len(numbers) != 3:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            results.append([date_obj.strftime("%Y-%m-%d"), draw_type] + numbers)
        except ValueError:
            continue

    return results

def write_to_csv(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Draw", "Digit1", "Digit2", "Digit3"])
        writer.writerows(sorted(data, key=lambda x: x[0]))
    print(f"✅ Wrote {len(data)} records to {output_path}")

def main():
    recent_years = get_recent_years(3)
    all_data = []

    for draw_type, base_url in BASE_URLS.items():
        for year in recent_years:
            all_data += fetch_year_data(draw_type, base_url, year)

    write_to_csv(all_data, OUTPUT_FILE)

if __name__ == "__main__":
    main()
