from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers

app = Flask(__name__)

# Load the CSV and preprocess
df = pd.read_csv('data/ga_cash3_history.csv')

# Fix: Auto-detect date format to avoid parsing warnings
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Sort by date and draw time (Midday, Evening, Night)
df = df.sort_values(by=['Date', 'DrawTime'], ascending=False)

# Get latest result
latest_result = df.iloc[0]
latest_numbers = [int(latest_result['Digit1']), int(latest_result['Digit2']), int(latest_result['Digit3'])]
latest_draw_time = latest_result['DrawTime']
latest_date = latest_result['Date'].strftime('%Y-%m-%d')

# Get predictions using strategy engine
predictions = predict_next_numbers(df)

@app.route('/')
def index():
    return render_template('index.html',
                           latest_date=latest_date,
                           latest_draw_time=latest_draw_time,
                           latest_numbers=latest_numbers,
                           predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
