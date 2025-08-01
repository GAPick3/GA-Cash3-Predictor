# fetch_pdf.py
import requests
import os
from datetime import datetime

# TODO: Replace this with the real, stable PDF URL if known.
PDF_URL = "https://www.galottery.com/content/dam/ga-lottery/pdfs/instant-games/GA_Lottery_WinningNumbers.pdf"
LOCAL_PATH = "data/latest.pdf"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def download_pdf():
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    try:
        resp = requests.get(PDF_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print("❌ PDF download failed:", e)
        return False

    # Simple change detection could be added here (e.g., compare bytes or headers)
    with open(LOCAL_PATH + ".tmp", "wb") as f:
        f.write(resp.content)
    os.replace(LOCAL_PATH + ".tmp", LOCAL_PATH)
    print(f"✅ PDF downloaded at {datetime.utcnow().isoformat()}Z")
    return True

if __name__ == "__main__":
    download_pdf()
