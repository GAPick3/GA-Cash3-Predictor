from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers
import os

app = Flask(__name__)

# Load and clean data
def load_data():
    try:
        df = pd.read_csv('data/ga_cash3_history_cleaned.csv')

        # Ensure proper date format
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Drop rows with missing dates or digits
        df.dropna(subset=['Date', 'Digit1', 'Digit2', 'Digit3'], inplace=True)

        # Convert digits to integers
        for col in ['Digit1', 'Digit2', 'Digit3']:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        # Sort chronologically
        df.sort_values(by='Date', ascending=False, inplace=True)

        return df
    except Exception as e:
        print(f"Data loading error: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    df = load_data()

    if df.empty:
        return render_template('index.html', error="Failed to load or process data.")

    latest_draw = df.iloc[0]
    latest_date = latest_draw['Date'].strftime('%Y-%m-%d')
    latest_time = latest_draw['DrawTime']
    latest_number = f"{latest_draw['Digit1']}-{latest_draw['Digit2']}-{latest_draw['Digit3']}"
    latest_payout = latest_draw['TotalPayout']
    latest_winners = latest_draw['Winners']

    # Predict next draw
    next_predictions = predict_next_numbers(df)

    return render_template('index.html',
                           latest_date=latest_date,
                           latest_time=latest_time,
                           latest_number=latest_number,
                           latest_payout=latest_payout,
                           latest_winners=latest_winners,
                           predictions=next_predictions)

if __name__ == '__main__':
    app.run(debug=True)
