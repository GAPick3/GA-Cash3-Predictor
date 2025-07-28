import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def fetch_latest_result():
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    for row in soup.select("table.results tbody tr"):
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            date = datetime.strptime(cols[0].text.strip(), "%m/%d/%Y").date()
            draw = cols[1].text.strip()
            digits = [int(n) for n in cols[2].text.strip().split() if n.isdigit()]
            if len(digits) == 3:
                time_map = {"Midday": "12:20pm", "Evening": "6:59pm", "Night": "11:34pm"}
                return [str(date), draw, digits[0], digits[1], digits[2], time_map.get(draw, "")]
        except:
            continue
    return None

def update_csv():
    new = fetch_latest_result()
    if not new:
        print("No new data found.")
        return

    df = pd.read_csv("data/ga_cash3_history.csv")
    if not ((df["Date"] == new[0]) & (df["Draw"] == new[1])).any():
        print("🔄 Adding new draw:", new)
        df.loc[-1] = new  # Add row
        df.index = df.index + 1
        df.sort_index(inplace=True)
        df.to_csv("data/ga_cash3_history.csv", index=False)
    else:
        print("✅ Latest draw already exists. No update needed.")

if __name__ == "__main__":
    update_csv()
