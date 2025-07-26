import csv
from collections import Counter

def predict_next_numbers(history, n=5):
    digits = [tuple(row[2:]) for row in history]
    counter = Counter(digits)
    most_common = counter.most_common(n)
    return [list(seq) for seq, _ in most_common]
