import pandas as pd
from collections import Counter

def predict_next_numbers(df=None, n=5):
    if df is None:
        df = pd.read_csv("data/ga_cash3_history.csv")

    triplets = df.apply(lambda row: f"{int(row['Number1'])}{int(row['Number2'])}{int(row['Number3'])}", axis=1)
    most_common = Counter(triplets).most_common(n)
    
    return [x[0] for x in most_common]
