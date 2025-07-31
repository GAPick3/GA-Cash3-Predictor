# predictor.py

import random
import pandas as pd

def predict_next_numbers(df: pd.DataFrame = None):
    """
    Predicts the next 3-digit number.
    Currently uses a simple random strategy.
    Replace this with pattern analysis or ML later.
    """
    # Placeholder: random 3-digit prediction
    return [random.randint(0, 9) for _ in range(3)]
