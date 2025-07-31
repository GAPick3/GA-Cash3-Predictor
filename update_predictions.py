# update_predictions.py

import pandas as pd
from predictions import predict_next_numbers, evaluate_accuracy
import json
from datetime import datetime

# Load data
df = pd.read_csv("ga_cash3_history_cleaned.csv")
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
df = df.dropna(subset=["Date", "Digit1", "Digit2", "Digit3"])
df = df.sort_values(by="Date")

# Predict next
prediction = predict_next_numbers(df)
with open("data/latest_prediction.json", "w") as f:
    json.dump(prediction, f)

# Evaluate accuracy
accuracy = evaluate_accuracy(df, 30)
with open("data/latest_accuracy.json", "w") as f:
    json.dump(accuracy, f)

print(f"[{datetime.now()}] ✅ Prediction + accuracy updated.")
