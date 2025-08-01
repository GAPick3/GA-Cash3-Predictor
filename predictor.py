# predictor.py
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta

def predict_next_numbers(df=None, n=5):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv", parse_dates=["Date"])

    # Basic heuristic: score triplets based on combination of frequency and recency
    df = df.copy()
    df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
    triplet_freq = Counter(df["Triplet"])
    # recency score: more recent occurrences boost
    now = df["Date"].max()
    recency_scores = {}
    for triplet in triplet_freq:
        # find most recent date this triplet appeared
        sub = df[df["Triplet"] == triplet]
        last_date = sub.sort_values("Date", ascending=False).iloc[0]["Date"]
        days_ago = (now - last_date).days
        recency_score = 1 / (1 + days_ago)  # recent gets higher
        recency_scores[triplet] = recency_score

    # Combined scoring: frequency normalized + recency
    max_freq = max(triplet_freq.values()) if triplet_freq else 1
    scores = {}
    for triplet, freq in triplet_freq.items():
        freq_score = freq / max_freq
        combined = 0.6 * freq_score + 0.4 * recency_scores.get(triplet, 0)
        scores[triplet] = combined

    # Return top n triplets by score
    sorted_triplets = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in sorted_triplets[:n]]
