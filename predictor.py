import pandas as pd
import random

def predict_next_numbers(df):
    digits = pd.concat([df['Digit1'], df['Digit2'], df['Digit3']])
    freq = digits.value_counts().sort_values(ascending=False)
    hot_digits = freq.index.tolist()[:5]  # Top 5 digits

    predictions = []
    for _ in range(5):
        prediction = random.sample(hot_digits, 3)
        predictions.append("".join(map(str, prediction)))
    return predictions
