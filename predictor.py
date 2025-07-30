import random

def predict_next_numbers(df):
    """
    Predict next Cash 3 numbers using a frequency-based strategy.
    You can later replace this with machine learning or deeper analytics.
    """
    digit_columns = ['Digit1', 'Digit2', 'Digit3']

    # Count digit frequencies
    all_digits = df[digit_columns].values.flatten()
    digit_counts = {i: 0 for i in range(10)}
    for digit in all_digits:
        digit_counts[int(digit)] += 1

    # Sort digits by frequency (most common first)
    sorted_digits = sorted(digit_counts.items(), key=lambda x: x[1], reverse=True)
    most_common_digits = [str(d[0]) for d in sorted_digits[:5]]  # top 5 digits

    # Randomly pick 3 digits from most common for prediction
    prediction = random.sample(most_common_digits, 3)
    return ' '.join(prediction)
