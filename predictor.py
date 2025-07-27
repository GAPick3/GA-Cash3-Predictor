# predictor.py
import pandas as pd
from collections import Counter

def predict_next_numbers(df=None, n=5):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv")
    triplets = df.apply(lambda r: f"{r['Number1']}{r['Number2']}{r['Number3']}", axis=1)
    return [seq for seq, _ in Counter(triplets).most_common(n)]
