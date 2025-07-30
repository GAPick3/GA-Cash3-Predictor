import schedule
import time
import shutil
from datetime import datetime

def update_csv():
    try:
        print("Checking for new updates...")
        shutil.copy('data/ga_cash3_latest.csv', 'data/ga_cash3_history.csv')
        print("CSV updated at", datetime.now())
    except Exception as e:
        print("CSV update failed:", e)

schedule.every().day.at("13:29").do(update_csv)
schedule.every().day.at("19:59").do(update_csv)
schedule.every().day.at("00:34").do(update_csv)

while True:
    schedule.run_pending()
    time.sleep(60)
