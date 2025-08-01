# predictor.py

from collections import Counter

def predict_next_numbers(df, draw=None, n=5):
    """
    Return top n triplets (and their counts) optionally filtered by draw type.
    """
    if df is None or df.empty:
        return []

    working = df.copy()
    if draw:
        working = working[working["Draw"].str.lower() == draw.lower()]

    # Construct triplet string
    working["Triplet"] = working.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)
    triplet_counts = Counter(working["Triplet"])
    most_common = triplet_counts.most_common(n)
    return [{"triplet": t, "count": c} for t, c in most_common]
