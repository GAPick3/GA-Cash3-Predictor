import pandas as pd
import random
from collections import Counter

def predict_next_numbers(df, num_predictions=5):
    # Convert to tuples for easier processing
    df['Combination'] = list(zip(df['Digit1'], df['Digit2'], df['Digit3']))

    # Frequency analysis
    all_combos = df['Combination'].tolist()
    combo_counts = Counter(all_combos)
    most_common = combo_counts.most_common(50)

    # Hot numbers
    digits = df[['Digit1', 'Digit2', 'Digit3']].values.flatten()
    digit_counts = Counter(digits)
    hot_digits = [int(x[0]) for x in digit_counts.most_common(5)]

    # Generate predictions using weighted logic
    predictions = []
    for _ in range(num_predictions):
        prediction = random.choices(hot_digits, k=3)
        predictions.append(prediction)

    return predictions
