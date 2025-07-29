# strategy_predictor.py

import pandas as pd
import random
from collections import defaultdict
from datetime import datetime


# Parameters
DECAY_FACTOR = 0.95  # How fast frequency weight decays
NUM_PREDICTIONS = 5  # Number of predictions to generate


def load_history(csv_path='data/ga_cash3_history.csv'):
    df = pd.read_csv(csv_path)
    df = df.dropna()
    df['Number'] = df['Number'].astype(str).str.zfill(3)
    df['DrawDate'] = pd.to_datetime(df['DrawDate'])
    return df.sort_values('DrawDate', ascending=True)


def get_digit_position_freqs(df):
    """Return frequency and recency-decayed frequency for each digit and position."""
    decay_scores = [DECAY_FACTOR ** i for i in reversed(range(len(df)))]
    pos_freq = [defaultdict(float) for _ in range(3)]

    for i, (_, row) in enumerate(df.iterrows()):
        num = row['Number']
        for pos in range(3):
            digit = int(num[pos])
            pos_freq[pos][digit] += decay_scores[i]  # Decayed contribution

    return pos_freq


def get_transition_matrix(df):
    """Return digit transition matrix for each position."""
    transitions = [defaultdict(lambda: defaultdict(int)) for _ in range(3)]

    for i in range(1, len(df)):
        prev = df.iloc[i-1]['Number']
        curr = df.iloc[i]['Number']
        for pos in range(3):
            prev_digit = int(prev[pos])
            curr_digit = int(curr[pos])
            transitions[pos][prev_digit][curr_digit] += 1

    return transitions


def weighted_sample(freq_dict):
    """Randomly sample a key from dict based on weighted values."""
    total = sum(freq_dict.values())
    if total == 0:
        return random.randint(0, 9)
    r = random.uniform(0, total)
    upto = 0
    for k, w in freq_dict.items():
        upto += w
        if upto >= r:
            return k
    return random.choice(list(freq_dict.keys()))


def predict_next_numbers():
    df = load_history()
    freq_by_position = get_digit_position_freqs(df)
    transitions = get_transition_matrix(df)
    last_draw = df.iloc[-1]['Number']

    predictions = []
    for _ in range(NUM_PREDICTIONS):
        number = ''
        for pos in range(3):
            prev_digit = int(last_draw[pos])
            combined_weights = defaultdict(float)

            # Use transition logic + decayed frequency
            for d in range(10):
                combined_weights[d] = freq_by_position[pos].get(d, 0) * 0.6 + \
                                       transitions[pos][prev_digit].get(d, 0) * 0.4

            digit = weighted_sample(combined_weights)
            number += str(digit)

        predictions.append(number)

    return predictions


if __name__ == '__main__':
    print(predict_next_numbers())
