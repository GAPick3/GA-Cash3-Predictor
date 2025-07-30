import pandas as pd
from datetime import datetime
from scraper import update_csv  # assumes this function updates ga_cash3_history.csv

# Set expected draw hours
DRAW_HOURS = {
    'Midday': 12,
    'Evening': 18,
    'Night': 23
}

def should_run_for(draw_time):
    now = datetime.now()
    target_hour = DRAW_HOURS[draw_time] + 1
    return now.hour == target_hour

def main():
    for draw_time in DRAW_HOURS:
        if should_run_for(draw_time):
            print(f"Running update for {draw_time} draw...")
            update_csv()  # fetches latest result & updates CSV

if __name__ == '__main__':
    main()
