from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os
from predictor import predict_next_numbers

app = Flask(__name__)

CSV_PATH = 'data/ga_cash3_history.csv'
PLOT_PATH = 'static/draw_frequency.png'
PREDICTION_LOG = 'data/prediction_log.csv'

def load_data():
    try:
        df = pd.read_csv(CSV_PATH)
        # 🔧 Fix: Parse with known format, handle bad rows
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
        df = df.dropna(subset=['Date'])
        df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()  # Return empty if failed

def create_chart(df):
    try:
        digits = pd.concat([df['Digit1'], df['Digit2'], df['Digit3']])
        counts = digits.value_counts().sort_index()
        plt.figure(figsize=(10, 4))
        counts.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('Digit Frequency (All Positions)')
        plt.xlabel('Digit')
        plt.ylabel('Count')
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        plt.savefig(PLOT_PATH)
        plt.close()
    except Exception as e:
        print(f"Error creating chart: {e}")

def log_prediction(prediction):
    try:
        pd.DataFrame([{
            'Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Prediction': ''.join(map(str, prediction))
        }]).to_csv(PREDICTION_LOG, mode='a', header=not os.path.exists(PREDICTION_LOG), index=False)
    except Exception as e:
        print(f"Failed to log prediction: {e}")

@app.route('/')
def index():
    df = load_data()
    if df.empty:
        return "Failed to load data"

    latest_result = df.iloc[0]
    latest_draw = f"{int(latest_result['Digit1'])}{int(latest_result['Digit2'])}{int(latest_result['Digit3'])}"
    latest_date = latest_result['Date'].strftime('%Y-%m-%d')
    draw_time = latest_result['DrawTime']

    prediction = predict_next_numbers(df)
    log_prediction(prediction)
    create_chart(df)

    return render_template('index.html',
                           latest_date=latest_date,
                           draw_time=draw_time,
                           latest_draw=latest_draw,
                           prediction=prediction,
                           chart_path=PLOT_PATH)

if __name__ == '__main__':
    app.run(debug=True)
