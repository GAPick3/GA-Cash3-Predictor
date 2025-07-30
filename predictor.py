import pandas as pd
import numpy as np
from collections import defaultdict

def apply_exponential_decay(frequencies, decay_rate=0.98):
    decayed = defaultdict(float)
    for i, draw in enumerate(reversed(frequencies)):
        weight = decay_rate ** i
        for pos, digit in enumerate(draw):
            decayed[(pos, digit)] += weight
    return decayed

def build_transition_matrix(draws):
    transitions = [defaultdict(lambda: defaultdict(int)) for _ in range(3)]
    for i in range(1, len(draws)):
        prev = draws[i - 1]
        curr = draws[i]
        for pos in range(3):
            transitions[pos][prev[pos]][curr[pos]] += 1
    return transitions

def predict_next_numbers(df):
    draws = df['WinningNumber'].astype(str).str.zfill(3).tolist()
    
    # Digit frequencies (with exponential decay)
    decayed_freq = apply_exponential_decay(draws)
    
    # Transition matrix from prior draws
    transitions = build_transition_matrix(draws)

    last_draw = draws[-1]
    prediction = ""
    for pos in range(3):
        scores = {}
        for digit in map(str, range(10)):
            freq_score = decayed_freq[(pos, digit)]
            trans_score = transitions[pos][last_draw[pos]].get(digit, 0)
            scores[digit] = 0.6 * freq_score + 0.4 * trans_score
        best_digit = max(scores, key=scores.get)
        prediction += best_digit

    return prediction
