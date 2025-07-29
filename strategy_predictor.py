# strategy_predictor.py
import pandas as pd
from collections import Counter
import itertools
from datetime import datetime


def load_data(filepath="data/ga_cash3_history.csv"):
    df = pd.read_csv(filepath)
    df["Digit1"] = df["Digit1"].astype(int)
    df["Digit2"] = df["Digit2"].astype(int)
    df["Digit3"] = df["Digit3"].astype(int)
    df["Number"] = df["Digit1"].astype(str) + df["Digit2"].astype(str) + df["Digit3"].astype(str)
    return df


def get_pattern(row):
    digits = [row["Digit1"], row["Digit2"], row["Digit3"]]
    unique_digits = len(set(digits))
    if unique_digits == 1:
        return "Triple"
    elif unique_digits == 2:
        return "Double"
    else:
        return "Unique"


def generate_strategic_predictions(filepath="data/ga_cash3_history.csv", max_preds=5):
    df = load_data(filepath)
    df["Pattern"] = df.apply(get_pattern, axis=1)

    # Count overall digit and position frequencies
    digits = df[["Digit1", "Digit2", "Digit3"]].values.flatten()
    hot_digits = [d for d, _ in Counter(digits).most_common(5)]
    cold_digits = [d for d, _ in Counter(digits).most_common()][-5:]

    pos_counts = {
        "Digit1": Counter(df["Digit1"]),
        "Digit2": Counter(df["Digit2"]),
        "Digit3": Counter(df["Digit3"]),
    }

    # Recent results and patterns
    recent_numbers = df["Number"].head(30).tolist()
    pattern_trend = df["Pattern"].head(30).value_counts().idxmax()

    pattern_numbers = df[df["Pattern"] == pattern_trend]["Number"].unique().tolist()
    pattern_candidates = [n for n in pattern_numbers if n not in recent_numbers]

    # Combine strategy: hot/cold, pattern matching
    base_digits = hot_digits + cold_digits
    combos = ["".join(map(str, c)) for c in itertools.product(base_digits, repeat=3)]

    final_candidates = [n for n in combos if n not in recent_numbers][:max_preds] + pattern_candidates[:max_preds]

    return list(dict.fromkeys(final_candidates))[:max_preds]  # De-dupe & limit


def save_predictions(predictions, path="data/prediction_log.csv"):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame({"timestamp": [time_now] * len(predictions), "prediction": predictions})
    df.to_csv(path, mode="a", header=not pd.io.common.file_exists(path), index=False)


if __name__ == "__main__":
    preds = generate_strategic_predictions()
    print("Predicted Numbers:", preds)
    save_predictions(preds)
