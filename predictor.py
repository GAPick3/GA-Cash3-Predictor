import pandas as pd
from collections import Counter

def predict_next_numbers(df=None, n=5):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv", parse_dates=["Date"])
    df = df.copy()
    # Ensure columns exist and are cleaned
    for col in ["Digit1", "Digit2", "Digit3"]:
        if col not in df.columns:
            return []

    # Build triplet string, zero-padded if needed
    def make_triplet(row):
        try:
            return f"{int(row['Digit1']):d}{int(row['Digit2']):d}{int(row['Digit3']):d}"
        except Exception:
            return None

    triplets = df.apply(make_triplet, axis=1).dropna()
    freq = Counter(triplets)
    most_common = [seq for seq, _ in freq.most_common(n)]
    return most_common
