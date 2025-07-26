import requests
from bs4 import BeautifulSoup
import csv
import datetime
import time
import os

BASE_URLS = {
    "Midday": "https://www.lotteryusa.com/georgia/midday-3/",
    "Evening": "https://www.lotteryusa.com/georgia/evening-3/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_draw_data(draw_type, base_url, years=2):
    all_results = []
    current_year = datetime.datetime.now().year

    for year in range(current_year, current_year - years, -1):
        url = f"{base_url}{year}/"
        print(f"🔎 Scraping {draw_type} draws for {year}: {url}")

        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("tr.draw-result")

        for row in rows:
            date = row.select_one(".date").text.strip()
            numbers = [n.text for n in row.select(".result .number")]
            if len(numbers) == 3:
                all_results.append([draw_type, date] + numbers)

        time.sleep(1)  # avoid being blocked

    return all_results

def write_csv(data, filename="data/ga_cash3_history.csv"):
    os.makedirs("data", exist_ok=True)
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["DrawType", "Date", "Digit1", "Digit2", "Digit3"])
        writer.writerows(data)
    print(f"✅ Wrote {len(data)} records to {filename}")

if __name__ == "__main__":
    full_data = []
    for draw_type, url in BASE_URLS.items():
        full_data += get_draw_data(draw_type, url)
    write_csv(full_data)
