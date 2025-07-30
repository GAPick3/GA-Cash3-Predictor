from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os
from predictor import predict_next_numbers

app = Flask(__name__)

@app.route('/')
def index():
    # Load cleaned data
    df = pd.read_csv('data/ga_cash3_history_cleaned.csv')

    # Ensure correct column types
    df['Date'] = pd.to_datetime(df['Date'])
    df[['Digit1', 'Digit2', 'Digit3']] = df[['Digit1', 'Digit2', 'Digit3']].astype(int)

    # Get latest draw
    latest = df.sort_values(by='Date', ascending=False).iloc[0]
    latest_draw = {
        'date': latest['Date'].strftime('%Y-%m-%d'),
        'draw_time': latest['DrawTime'],
        'numbers': f"{latest['Digit1']}{latest['Digit2']}{latest['Digit3']}"
    }

    # Generate hot numbers chart
    digits = pd.concat([df['Digit1'], df['Digit2'], df['Digit3']])
    freq = digits.value_counts().sort_index()
    plt.figure(figsize=(10, 5))
    plt.bar(freq.index.astype(str), freq.values, color='orange')
    plt.title('Hot Numbers')
    plt.xlabel('Digit')
    plt.ylabel('Frequency')
    plt.tight_layout()
    chart_path = os.path.join('static', 'hot_numbers.png')
    plt.savefig(chart_path)
    plt.close()

    # Predict next numbers
    predictions = predict_next_numbers(df)

    return render_template('index.html', latest_draw=latest_draw, predictions=predictions)
