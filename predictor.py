import pandas as pd
import random

def predict_next_numbers(df):
    """
    Basic pattern-based predictor: Most frequent digit in each column.
    Replace this with ML later.
    """
    d1 = df['Digit1'].mode().values[0]
    d2 = df['Digit2'].mode().values[0]
    d3 = df['Digit3'].mode().values[0]
    return [int(d1), int(d2), int(d3)]

def evaluate_accuracy(df, n=30):
    exact_matches = 0
    any_order_matches = 0

    for i in range(n, 0, -1):
        train_df = df.iloc[:-(i)]
        actual = df.iloc[-i]
        prediction = predict_next_numbers(train_df)

        actual_digits = [int(actual['Digit1']), int(actual['Digit2']), int(actual['Digit3'])]

        if prediction == actual_digits:
            exact_matches += 1
        elif sorted(prediction) == sorted(actual_digits):
            any_order_matches += 1

    return {
        "total": n,
        "exact": exact_matches,
        "any_order": any_order_matches
    }
