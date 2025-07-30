from flask import Flask, render_template
import pandas as pd
import os
from predictor import predict_next_numbers

app = Flask(__name__)

CSV_PATH = "data/ga_cash3_history_cleaned.csv"

def load_data():
    """Safely load and validate the cleaned GA Cash 3 data."""
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] CSV file not found: {CSV_PATH}")
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_PATH)

    if df.empty:
        print("[ERROR] CSV is empty.")
        return pd.DataFrame()
    
    if 'Date' not in df.columns:
        print("[ERROR] 'Date' column missing in CSV.")
        return pd.DataFrame()

    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
    df = df.dropna(subset=['Date'])  # drop rows with invalid or missing dates

    return df

df = load_data()

@app.route('/')
def index():
    if df.empty:
        return render_template('index.html', error="No valid data found. Please check the CSV file.")

    latest = df.sort_values(by='Date', ascending=False).iloc[0]
    latest_result = {
        'date': latest['Date'].strftime('%Y-%m-%d'),
        'draw_time': latest['DrawTime'],
        'numbers': f"{int(latest['Digit1'])}{int(latest['Digit2'])}{int(latest['Digit3'])}",
        'winners': latest['Winners'],
        'payout': latest['TotalPayout']
    }

    predictions = predict_next_numbers(df)

    return render_template(
        'index.html',
        latest_result=latest_result,
        predictions=predictions
    )

if __name__ == '__main__':
    app.run(debug=True)
