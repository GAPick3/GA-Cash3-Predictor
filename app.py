from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers
from collections import Counter
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import json

app = Flask(__name__)

def generate_chart(df):
    digits = df[['Digit1', 'Digit2', 'Digit3']].values.flatten()
    digit_counts = Counter(digits)

    fig, ax = plt.subplots()
    ax.bar(digit_counts.keys(), digit_counts.values(), color='skyblue')
    ax.set_title("Hot Numbers")
    ax.set_xlabel("Digit")
    ax.set_ylabel("Frequency")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return encoded

def log_predictions(predictions, draw_time):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "draw_time": draw_time,
        "predictions": predictions
    }
    with open("data/prediction_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

@app.route('/')
def index():
    try:
        df = pd.read_csv('data/ga_cash3_history.csv')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
    except Exception as e:
        return f"Error loading data: {e}"

    latest = df.iloc[-1]
    latest_draw = f"{latest['Digit1']}{latest['Digit2']}{latest['Digit3']}"
    latest_draw_time = latest['DrawTime']
    latest_date = latest['Date'].strftime('%Y-%m-%d')

    predictions = predict_next_numbers(df)
    log_predictions(predictions, latest_draw_time)

    chart = generate_chart(df)

    return render_template('index.html',
                           latest_draw=latest_draw,
                           latest_date=latest_date,
                           latest_draw_time=latest_draw_time,
                           predictions=predictions,
                           chart=chart)
