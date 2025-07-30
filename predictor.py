import pandas as pd
from collections import Counter
import random

def get_hot_numbers(df, top_n=10):
    all_numbers = df['Winning Numbers'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(3)
    digits = "".join(all_numbers)
    return [num for num, _ in Counter(digits).most_common(top_n)]

def get_last_digits(df):
    return df['Winning Numbers'].astype(str).str[-1]

def get_recent_patterns(df, count=10):
    return df['Winning Numbers'].tail(count).tolist()

def predict_next_numbers(df, n=5):
    hot_digits = get_hot_numbers(df)
    last_digits = get_last_digits(df).value_counts().index.tolist()
    recent_patterns = get_recent_patterns(df)

    predictions = set()

    while len(predictions) < n:
        # Generate a 3-digit number from hot digits and recent end digits
        num = ''.join(random.choices(hot_digits, k=2) + random.choices(last_digits, k=1))
        num = ''.join(sorted(num))  # Normalize order to reflect common draw behavior

        if num not in recent_patterns:
            predictions.add(num)

    return list(predictions)
