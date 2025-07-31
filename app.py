from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
import json
import os
from predictor import predict_next_numbers

app = Flask(__name__)

CSV_FILE = "data/ga_cash3_history_cleaned.csv"
HISTORY_LOG = "data/prediction_history.json"

def load_data():
    df = pd.read_csv(CSV_FILE)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values(by='Date', ascending=False)
    return df

def get_last_prediction():
    if os.path.exists(HISTORY_LOG):
        with open(HISTORY_LOG, 'r') as f:
            history = json.load(f)
            if history:
                return history[-1]  # most recent prediction
    return None

def save_prediction(prediction):
    history = []
    if os.path.exists(HISTORY_LOG):
        with open(HISTORY_LOG, 'r') as f:
            history = json.load(f)
    history.append(prediction)
    with open(HISTORY_LOG, 'w') as f:
        json.dump(history, f, indent=2)

def create_chart(df):
    df_sorted = df.sort_values(by='Date')
    values = df_sorted[['Digit1', 'Digit2', 'Digit3']].sum(axis=1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sorted['Date'], y=values, mode='lines+markers', name='Draw Sum'))
    fig.update_layout(
        title="Sum of Draw Digits Over Time",
        xaxis_title="Date",
        yaxis_title="Sum (Digit1 + Digit2 + Digit3)",
        template="plotly_dark"
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def index():
    df = load_data()
    latest_result = df.iloc[0]
    prediction = predict_next_numbers(df)
    last_prediction = get_last_prediction()
    save_prediction({
        "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "prediction": prediction
    })

    chart_json = create_chart(df)
    return render_template("index.html",
                           latest_result=latest_result,
                           prediction=prediction,
                           last_prediction=last_prediction,
                           chart_json=chart_json)

if __name__ == '__main__':
    app.run(debug=True)
