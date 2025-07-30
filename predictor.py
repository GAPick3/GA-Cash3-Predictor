import pandas as pd
import numpy as np
from collections import Counter
import random

# Strategies

def hot_numbers(df, top_n=5):
    counts = Counter(df['Number'])
    most_common = [num for num, _ in counts.most_common(top_n)]
    return most_common

def cold_numbers(df, bottom_n=5):
    counts = Counter(df['Number'])
    least_common = [num for num, _ in counts.most_common()][-bottom_n:]
    return least_common

def recent_winning_patterns(df):
    last_20 = df['Number'].tail(20).astype(str)
    digits = [d for num in last_20 for d in num.zfill(3)]
    return Counter(digits).most_common()

def mirror_numbers(df):
    # Simple mirror logic (0↔5, 1↔6, ..., 4↔9)
    mirror_map = {'0':'5','1':'6','2':'7','3':'8','4':'9',
                  '5':'0','6':'1','7':'2','8':'3','9':'4'}
    last_draw = str(df.iloc[-1]['Number']).zfill(3)
    return [''.join(mirror_map[d] for d in last_draw)]

def overdue_numbers(df, top_n=5):
    all_nums = set(range(1000))
    recent = set(df['Number'].tail(50))
    overdue = list(all_nums - recent)
    return random.sample(overdue, min(len(overdue), top_n))

def predict_next_numbers(df):
    df['Number'] = df['Number'].astype(str).str.zfill(3)

    hot = hot_numbers(df, top_n=15)
    cold = cold_numbers(df, bottom_n=15)
    overdue = overdue_numbers(df, top_n=15)
    mirror = mirror_numbers(df)

    candidates = set(hot + cold + overdue + mirror)
    candidates = [str(num).zfill(3) for num in candidates if len(str(num)) <= 3]

    if not candidates:
        return tuple(random.choices(range(10), k=3))

    chosen = random.choice(candidates)
    return tuple(chosen)
