from flask import Flask, render_template
import pandas as pd
import os
from predictor import predict_next_numbers

app = Flask(__name__)

# Updated CSV path
csv_path = 'data/ga_cash3_history_cleaned.csv'

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
    df = df.dropna(subset=['Date'])

    latest = df.sort_values(by='Date', ascending=False).iloc[0]
    latest_result = {
        'date': latest['Date'].strftime('%Y-%m-%d'),
        'draw_time': latest['DrawTime'],
        'numbers': f"{int(latest['Digit1'])}{int(latest['Digit2'])}{int(latest['Digit3'])}",
        'winners': latest['Winners'],
        'payout': latest['TotalPayout']
    }

    predictions = predict_next_numbers(df)
else:
    latest_result = {
        'date': 'N/A',
        'draw_time': 'N/A',
        'numbers': 'N/A',
        'winners': 'N/A',
        'payout': 'N/A'
    }
    predictions = ['CSV file not found. Upload required.']

@app.route('/')
def index():
    return render_template('index.html', latest_result=latest_result, predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
