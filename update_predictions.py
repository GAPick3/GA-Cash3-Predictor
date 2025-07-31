import pandas as pd
from predictions import predict_next_numbers, evaluate_accuracy
import json

df = pd.read_csv("ga_cash3_history_cleaned.csv")
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
df = df.dropna()
df = df.sort_values(by="Date")

# Save prediction
prediction = predict_next_numbers(df)
with open("latest_prediction.json", "w") as f:
    json.dump(prediction, f)

# Save accuracy
accuracy_data = evaluate_accuracy(df, 30)
with open("latest_accuracy.json", "w") as f:
    json.dump(accuracy_data, f)
