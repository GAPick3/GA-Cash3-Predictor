from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers
import os

app = Flask(__name__)

# Load the CSV with explicit date format
df = pd.read_csv('data/ga_cash3_history.csv')
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')  # Explicit date format
df = df.dropna(subset=['Date'])  # Remove rows where date parsing failed

# Get latest result
latest = df.sort_values(by='Date', ascending=False).iloc[0]
latest_result = {
    'date': latest['Date'].strftime('%Y-%m-%d'),
    'draw_time': latest['DrawTime'],
    'numbers': f"{int(latest['Digit1'])}{int(latest['Digit2'])}{int(latest['Digit3'])}",
    'winners': latest['Winners'],
    'payout': latest['TotalPayout']
}

# Get predictions
predictions = predict_next_numbers(df)

@app.route('/')
def index():
    return render_template('index.html', latest_result=latest_result, predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
