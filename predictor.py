# predictor.py

import pandas as pd
import random

def predict_next_numbers(data_path='data/ga_cash3_history.csv'):
    df = pd.read_csv(data_path)
    # Naive prediction: most common triplets
    freq = df['Number'].value_counts().head(5)
    return list(freq.index)
