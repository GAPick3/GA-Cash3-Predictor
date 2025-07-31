import pandas as pd
import random

def predict_next_numbers(df):
    """
    Predict the next number using mode-based frequency of each digit position.
    """
    d1 = df['Digit1'].mode().values[0]
    d2 = df['Digit2'].mode().values[0]
    d3 = df['Digit3'].mode().values[0]
    return [int(d1), int(d2), int(d3)]


def evaluate_accuracy(df, n=30):
    """
    Evaluate prediction accuracy over the last `n` draws.
    Returns a dictionary containing:
    - Total draws evaluated
    - Count of Exact and AnyOrder matches
    - Detailed match history for plotting
    """
    exact_matches = 0
    any_order_matches = 0
    match_results = []

    for i in range(n, 0, -1):
        train_df = df.iloc[:-(i)]
        actual = df.iloc[-i]
        prediction = predict_next_numbers(train_df)

        actual_digits = [int(actual['Digit1']), int(actual['Digit2']), int(actual['Digit3'])]
        date = str(actual['Date'].date())

        if prediction == actual_digits:
            match_type = 'Exact'
            exact_matches += 1
        elif sorted(prediction) == sorted(actual_digits):
            match_type = 'AnyOrder'
            any_order_matches += 1
        else:
            match_type = 'Miss'

        match_results.append({
