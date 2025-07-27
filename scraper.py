import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import os

def fetch_data():
    url = "https://www.lotterypost.com/results/ga/cash3/past"
    print(f"🔎 Scraping: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print("❌ Failed:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    today = datetime.now().date()
    cutoff = today - timedelta(days=3*365)
    data = []

    # Each date has up to 3 draws listed with their times and numbers
    sections = soup.select("div.content > h2 + div.panel")
    for sec in sections:
        try:
            date_header = sec.find_previous_sibling("h2")
            date_str = date_header.text.strip()
            date = datetime.strptime(date_str, "%B %Y").date()
            # Actually LotteryPost lists group by months, so process within panel
        except:
            continue

    # Instead, simpler: iterate every draw row
    for row in soup.select("div.results li"):
        try:
            date_text = row.select_one(".rpDate").text.strip()
            dt = datetime.strptime(date_text, "%A, %B %d, %Y").date()
            if dt < cutoff:
                continue

            draw_label = row.select_one(".rpTime").text.strip().lower()
            nums = row.select(".rpNum")
            digits = [n.text.strip() for n in nums if n.text.strip().isdigit()]
            if len(digits)==3:
                data.append([dt.isoformat(), draw_label] + digits)
        except Exception:
            continue

    return data

def main():
    all_data = fetch_data()
    os.makedirs("data", exist_ok=True)
    with open("data/ga_cash3_history.csv","w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date","Draw","Number1","Number2","Number3"])
        writer.writerows(all_data)
    print(f"✅ Wrote {len(all_data)} records to data/ga_cash3_history.csv")

if __name__=="__main__":
    main()
