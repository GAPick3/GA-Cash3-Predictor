# predictor.py

import pandas as pd
from collections import Counter

CSV_PATH = "data/ga_cash3_history.csv"

def load():
    df = pd.read_csv(CSV_PATH)
    return df

def top_triplets(n=5):
    df = load()
    df["Triplet"] = df.apply(lambda r: f"{int(r.Digit1)}{int(r.Digit2)}{int(r.Digit3)}", axis=1)
    counts = Counter(df["Triplet"])
    return counts.most_common(n)

def hot_digits():
    df = load()
    overall = Counter()
    for _, r in df.iterrows():
        overall.update([r.Digit1, r.Digit2, r.Digit3])
    return overall.most_common()

if __name__ == "__main__":
    print("Top triplets:", top_triplets())
    print("Hot digits:", hot_digits())
