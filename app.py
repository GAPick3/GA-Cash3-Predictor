from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
import plotly
import json
import os
from datetime import datetime
from predictor import predict_next_numbers, evaluate_accuracy

app = Flask(__name__)

CSV_FILE = "data/ga_cash3_history_cleaned.csv"
HISTORY_FILE = "data/prediction_history.json"

def load_data():
    df = pd.read_csv(CSV_FILE)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values(by='Date', ascending=False)
    return df

def get_last_prediction():
    if not os.path.exists(HISTORY_FILE) or os.stat(HISTORY_FILE).st_size == 0:
        return None
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            if history:
                return history[-1]
    except json.JSONDecodeError:
        return None
    return None

def save_prediction(prediction, actual):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prediction": prediction,
        "actual": actual
    }
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
    history.append(entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def create_interactive_chart(df):
    df_sorted = df.sort_values(by='Date')
    digit_sums = df_sorted[['Digit1', 'Digit2', 'Digit3']].sum(axis=1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sorted['Date'], y=digit_sums, mode='lines+markers', name='Sum of Digits'))

    fig.update_layout(
        title="Sum of Winning Digits Over Time",
        xaxis_title="Date",
        yaxis_title="Digit Sum (Digit1 + Digit2 + Digit3)",
        template="plotly_dark"
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def index():
    if not os.path.exists(CSV_FILE):
        return render_template("index.html", error="Data file not found.")

    df = load_data()
    latest = df.iloc[0]
    actual_result = [int(latest['Digit1']), int(latest['Digit2']), int(latest['Digit3'])]
    latest_result = {
        "date": latest['Date'].strftime('%Y-%m-%d'),
        "draw_time": latest['DrawTime'],
        "numbers": actual_result,
        "winners": latest['Winners'],
        "payout": latest['TotalPayout']
    }

    prediction = predict_next_numbers(df)
    save_prediction(prediction, actual_result)

    last_prediction = get_last_prediction()
    chart_json = create_interactive_chart(df)
    accuracy = evaluate_accuracy(df)

    return render_template("index.html",
                           latest_result=latest_result,
                           prediction=prediction,
                           last_prediction=last_prediction,
                           chart_json=chart_json,
                           accuracy=accuracy)

if __name__ == '__main__':
    app.run(debug=True)
