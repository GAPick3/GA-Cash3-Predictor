import pandas as pd
import numpy as np
import random
from datetime import datetime


def load_data(csv_path='data/ga_cash3_history.csv'):
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=True)
    return df


def get_frequency_weights(df, decay_rate=0.99):
    weights = {}
    today = df['Date'].max()
    for i in range(10):
        weights[str(i)] = 0
    
    for _, row in df.iterrows():
        age_days = (today - row['Date']).days
        weight = decay_rate ** age_days
        digits = [int(d) for d in f"{row['Result']:03d}"]
        for d in digits:
            weights[str(d)] += weight

    total = sum(weights.values())
    for d in weights:
        weights[d] /= total

    return weights


def get_transition_matrix(df):
    matrix = {pos: {str(i): {str(j): 1 for j in range(10)} for i in range(10)} for pos in range(3)}
    
    for i in range(1, len(df)):
        prev_digits = [int(d) for d in f"{df.iloc[i-1]['Result']:03d}"]
        curr_digits = [int(d) for d in f"{df.iloc[i]['Result']:03d}"]
        for pos in range(3):
            from_digit = str(prev_digits[pos])
            to_digit = str(curr_digits[pos])
            matrix[pos][from_digit][to_digit] += 1

    # Normalize
    for pos in range(3):
        for from_digit in matrix[pos]:
            total = sum(matrix[pos][from_digit].values())
            for to_digit in matrix[pos][from_digit]:
                matrix[pos][from_digit][to_digit] /= total

    return matrix


def smart_predict(df):
    freq_weights = get_frequency_weights(df)
    trans_matrix = get_transition_matrix(df)

    last_draw_digits = [int(d) for d in f"{df.iloc[-1]['Result']:03d}"]
    predicted_digits = []

    for pos in range(3):
        last_digit = str(last_draw_digits[pos])
        transition_probs = trans_matrix[pos][last_digit]

        # Blend transition with frequency
        hybrid_weights = {
            d: 0.6 * transition_probs[d] + 0.4 * freq_weights[d] for d in transition_probs
        }
        digits = list(hybrid_weights.keys())
        probs = list(hybrid_weights.values())
        predicted_digit = int(np.random.choice(digits, p=probs))
        predicted_digits.append(predicted_digit)

    prediction = int("".join(map(str, predicted_digits)))
    return prediction


def log_prediction(prediction, csv_path='data/prediction_log.csv'):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_row = pd.DataFrame([{'DateTime': now, 'Prediction': prediction}])
    try:
        df = pd.read_csv(csv_path)
        df = pd.concat([df, new_row], ignore_index=True)
    except FileNotFoundError:
        df = new_row
    df.to_csv(csv_path, index=False)


def predict_next_number():
    df = load_data()
    prediction = smart_predict(df)
    log_prediction(prediction)
    return prediction


if __name__ == '__main__':
    print("Next prediction:", predict_next_number())
