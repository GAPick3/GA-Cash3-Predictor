# predictor.py

import pandas as pd
import random

def predict_next_numbers(history, n=5):
    # Naive prediction: most common triplets
    freq = df['Number'].value_counts().head(5)
    return list(freq.index)
