import pandas as pd
import random
import os
from collections import defaultdict
from datetime import datetime

HISTORY_CSV = 'data/ga_cash3_history.csv'
LOG_CSV = 'data/prediction_log.csv'

# --- PARAMETERS ---
RECENCY_DECAY_RATE = 0.99  # exponential decay for older draws
MAX_DRAWS = 300            # max draws to consider (for performance)

# --- UTILITY FUNCTIONS ---
def load_data():
    df = pd.read_csv(HISTORY_CSV)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=False).head(MAX_DRAWS)
    df['Draw'] = df['Draw'].astype(str).str.zfill(3)
    return df

def compute_position_frequencies(df):
    freqs = [defaultdict(float) for _ in range(3)]
    for i, row in enumerate(df.itertuples(index=False), start=1):
        decay = RECENCY_DECAY_RATE ** i
        for pos in range(3):
            digit = int(row.Draw[pos])
            freqs[pos][digit] += decay
    return freqs

def compute_transition_probs(df):
    transitions = [defaultdict(lambda: defaultdict(int)) for _ in range(3)]
    for i in range(1, len(df)):
        prev = df.iloc[i]['Draw']
        curr = df.iloc[i - 1]['Draw']
        for pos in range(3):
            prev_digit = int(prev[pos])
            curr_digit = int(curr[pos])
            transitions[pos][prev_digit][curr_digit] += 1
    # Normalize to probabilities
    probs = [defaultdict(dict) for _ in range(3)]
    for pos in range(3):
        for prev_digit, next_digits in transitions[pos].items():
            total = sum(next_digits.values())
            probs[pos][prev_digit] = {k: v / total for k, v in next_digits.items()}
    return probs

def weighted_random_choice(weight_dict):
    digits = list(weight_dict.keys())
    weights = list(weight_dict.values())
    total = sum(weights)
    if total == 0:
        return random.randint(0, 9)
    return random.choices(digits, weights=weights, k=1)[0]

def generate_prediction(freqs, transitions, last_draw):
    prediction = []
    for pos in range(3):
        freq_weights = freqs[pos]
        trans_weights = transitions[pos].get(int(last_draw[pos]), {})

        # Combine weights
        combined = defaultdict(float)
        for digit in range(10):
            combined[digit] = freq_weights.get(digit, 0) * 0.6 + trans_weights.get(digit, 0) * 0.4
        prediction.append(str(weighted_random_choice(combined)))
    return ''.join(prediction)

def log_prediction(prediction, actual=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        'Timestamp': now,
        'Prediction': prediction,
        'Actual': actual if actual else ''
    }
    df = pd.DataFrame([entry])
    file_exists = os.path.exists(LOG_CSV)
    df.to_csv(LOG_CSV, mode='a', index=False, header=not file_exists)

def predict_next_numbers():
    df = load_data()
    freqs = compute_position_frequencies(df)
    transitions = compute_transition_probs(df)
    last_draw = df.iloc[0]['Draw']
    prediction = generate_prediction(freqs, transitions, last_draw)
    log_prediction(prediction)
    return prediction
