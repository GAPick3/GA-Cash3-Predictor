import pandas as pd
from collections import Counter

def predict_next_numbers(df=None, n=5):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv")
    df.rename(columns=lambda c: c.strip(), inplace=True)

    # Ensure digit columns exist
    for col in ("Digit1", "Digit2", "Digit3"):
        if col not in df.columns:
            raise KeyError(f"Expected column '{col}' in CSV")

    # Build triplets like "123"
    triplets = df.apply(
        lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1
    )
    freq = Counter(triplets)

    most_common = [combo for combo, _ in freq.most_common(n)]
    least_common = []
    if len(freq) >= n:
        # get least common n (could be ties; this picks last n of most_common reversed)
        least_common = [combo for combo, _ in freq.most_common()[:-n-1:-1]]

    # Individual digit frequency
    digits_df = pd.DataFrame({
        "Digit1": df["Digit1"].astype(int),
        "Digit2": df["Digit2"].astype(int),
        "Digit3": df["Digit3"].astype(int)
    })
    digit_frequency = {
        "Digit1": digits_df["Digit1"].value_counts().sort_index().to_dict(),
        "Digit2": digits_df["Digit2"].value_counts().sort_index().to_dict(),
        "Digit3": digits_df["Digit3"].value_counts().sort_index().to_dict(),
    }

    return {
        "most_common_triplets": most_common,
        "least_common_triplets": least_common,
        "digit_frequency": digit_frequency
    }
