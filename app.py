from flask import Flask, render_template
import pandas as pd
import json
from predictor import predict_next_numbers, evaluate_accuracy

app = Flask(__name__)

@app.route("/")
def index():
    df = pd.read_csv("data/ga_cash3_history_cleaned.csv")
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values(by="Date")

    latest_result = df.iloc[-1]
    prediction = predict_next_numbers(df)
    
    # Load previous prediction if stored
    try:
        with open('static/last_prediction.json', 'r') as f:
            last_prediction = json.load(f)
    except FileNotFoundError:
        last_prediction = None

    # Save current prediction for next comparison
    with open('static/last_prediction.json', 'w') as f:
        json.dump(prediction, f)

    # Accuracy analysis
    accuracy = evaluate_accuracy(df, n=30)

    # Save history to JSON for chart rendering
    with open('static/accuracy_history.json', 'w') as f:
        json.dump(accuracy["history"], f)

    return render_template("index.html",
                           latest_result=latest_result,
                           prediction=prediction,
                           last_prediction=last_prediction,
                           accuracy=accuracy,
                           accuracy_history=accuracy["history"])
