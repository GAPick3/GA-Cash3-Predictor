# predictor.py
import pandas as pd
from collections import Counter, defaultdict

def format_triplet(row):
    return f"{int(row['Digit1'])}{int(row['Digit2'])}{int(row['Digit3'])}"

def top_triplets(df, draw_type=None, n=5):
    subset = df if draw_type is None else df[df["Draw"] == draw_type]
    triplets = subset.apply(format_triplet, axis=1)
    return [t for t, _ in Counter(triplets).most_common(n)]

def digit_frequency(df, draw_type=None):
    subset = df if draw_type is None else df[df["Draw"] == draw_type]
    freqs = {"Digit1": Counter(), "Digit2": Counter(), "Digit3": Counter()}
    for _, row in subset.iterrows():
        freqs["Digit1"][int(row["Digit1"])] += 1
        freqs["Digit2"][int(row["Digit2"])] += 1
        freqs["Digit3"][int(row["Digit3"])] += 1
    return {pos: dict(freqs[pos]) for pos in freqs}

def hot_cold(df, draw_type=None, recent_window=50):
    subset = df if draw_type is None else df[df["Draw"] == draw_type]
    all_counts = Counter(subset.apply(format_triplet, axis=1))
    recent = subset.head(recent_window)
    recent_counts = Counter(recent.apply(format_triplet, axis=1))

    hot = []
    cold = []
    for triplet in all_counts:
        long = all_counts[triplet]
        short = recent_counts.get(triplet, 0)
        if short > long * 0.5 and short >= 2:
            hot.append((triplet, short, long))
        if short < long * 0.2:
            cold.append((triplet, short, long))
    return {"hot": sorted(hot, key=lambda x: -x[1])[:5], "cold": sorted(cold, key=lambda x: x[1])[:5]}

def transition_matrix(df, draw_type=None):
    subset = df if draw_type is None else df[df["Draw"] == draw_type]
    triplets = subset.apply(format_triplet, axis=1).tolist()
    transitions = defaultdict(Counter)
    for prev, nex in zip(triplets, triplets[1:]):
        transitions[prev][nex] += 1
    # normalize maybe on request
    return {k: dict(v) for k, v in transitions.items()}

def predict_next_numbers(df, draw_type=None, n=5):
    # Basic: top triplets overall + hot ones
    top = top_triplets(df, draw_type, n)
    hc = hot_cold(df, draw_type)
    hot_triplets = [t for t, _, _ in hc["hot"]]
    # combine, dedupe preserving order
    combined = []
    for t in hot_triplets + top:
        if t not in combined:
            combined.append(t)
        if len(combined) >= n:
            break
    return combined[:n]
