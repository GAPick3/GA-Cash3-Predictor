import os
import pandas as pd
import json

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

history_path = "data/ga_cash3_history_cleaned.csv"
pred_path = "static/last_prediction.json"
acc_path = "static/accuracy_history.json"

# Create dummy draw history if not exists
if not os.path.exists(history_path):
    df = pd.DataFrame([{
        "Date": "2025-07-30",
        "Draw": "123",
        "DrawTime": "Evening",
        "Digit1": 1,
        "Digit2": 2,
        "Digit3": 3,
        "Winners": 0,
        "TotalPayout": 0
    }])
    df.to_csv(history_path, index=False)

# Create dummy prediction file
if not os.path.exists(pred_path):
    json.dump([1, 2, 3], open(pred_path, "w"))

# Create dummy accuracy file
if not os.path.exists(acc_path):
    json.dump([{
        "date": "2025-07-30",
        "prediction": [1, 2, 3],
        "actual": [1, 2, 3],
        "match": "Exact"
    }], open(acc_path, "w"))
