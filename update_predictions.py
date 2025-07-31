# update_predictions.py

import pandas as pd
import json
from predictor import predict_next_numbers, evaluate_accuracy

df = pd.read_csv("data/ga_cash3_history_cleaned.csv")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])
df = df.sort_values(by='Date')

prediction = predict_next_numbers(df)
with open("static/last_prediction.json", "w") as f:
    json.dump(prediction, f)

accuracy = evaluate_accuracy(df, n=30)
with open("static/accuracy_history.json", "w") as f:
    json.dump(accuracy["history"], f)
