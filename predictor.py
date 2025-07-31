import pandas as pd
from collections import Counter

def predict_next_numbers(df=None, n=5, draw=None):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv")

    if draw:
        df = df[df["Draw"].str.lower() == draw.lower()]

    # Ensure digits exist and are integers
    def triplet(row):
        try:
            return f"{int(row['Digit1'])}{int(row['Digit2'])}{int(row['Digit3'])}"
        except Exception:
            return None

    triplets = df.apply(triplet, axis=1).dropna()
    counts = Counter(triplets)
    return [combo for combo, _ in counts.most_common(n)]

def summary_stats(df=None):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv")
    total_draws = len(df)
    most_common_all = predict_next_numbers(df, n=3)
    by_draw = {}
    for label in df["Draw"].unique():
        by_draw[label] = predict_next_numbers(df, n=3, draw=label)
    return {
        "total_draws": total_draws,
        "top_overall": most_common_all,
        "top_by_draw": by_draw,
    }
