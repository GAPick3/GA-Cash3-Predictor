# scheduler.py
import os
from datetime import datetime, timedelta
from strategy_predictor import generate_strategic_predictions, save_predictions

# Georgia Cash 3 Draw Times (24-hour format)
DRAW_TIMES = [
    "12:20",  # Midday
    "18:59",  # Evening
    "23:34"   # Night
]

# Check if it's 1 hour past any draw time
def is_time_to_predict():
    now = datetime.now()
    for draw in DRAW_TIMES:
        draw_time = datetime.strptime(draw, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        if now >= draw_time + timedelta(hours=1) and now <= draw_time + timedelta(hours=2):
            return True
    return False


def run_prediction():
    if is_time_to_predict():
        print("⏰ Draw passed. Generating predictions...")
        preds = generate_strategic_predictions()
        save_predictions(preds)
        print("✅ Predictions saved:", preds)
    else:
        print("⌛ Not time yet. Skipping prediction.")


if __name__ == "__main__":
    run_prediction()
