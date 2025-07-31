import pandas as pd
import random
from collections import Counter
from datetime import datetime, timedelta

# Load the draw history
def load_data(file_path='data/ga_cash3_history.csv'):
    df = pd.read_csv(file_path)
    df['Draw Date'] = pd.to_datetime(df['Draw Date'])
    return df

# Predict next numbers based on frequency of past draws
def predict_next_numbers(n_predictions=5):
    df = load_data()
    all_numbers = df['Winning Numbers'].astype(str).str.zfill(3)

    # Flatten all digits from the past numbers
    digits = [digit for number in all_numbers for digit in number]
    counter = Counter(digits)

    # Get the top most frequent digits
    top_digits = [item[0] for item in counter.most_common(5)]

    predictions = set()
    while len(predictions) < n_predictions:
        pred = ''.join(random.choices(top_digits, k=3))
        predictions.add(pred)

    return list(predictions)

# Evaluate how well predictions matched recent results
def evaluate_accuracy(predictions, n_results=5):
    df = load_data()
    recent_results = df.sort_values('Draw Date', ascending=False).head(n_results)
    recent_numbers = recent_results['Winning Numbers'].astype(str).str.zfill(3).tolist()

    match_results = []
    for pred in predictions:
        match_info = {
            'prediction': pred,
            'matches': []
        }
        for result in recent_numbers:
            matches = sum(p == r for p, r in zip(pred, result))
            match_info['matches'].append({
                'draw': result,
                'matched_digits': matches
            })
        match_results.append(match_info)

    return match_results
