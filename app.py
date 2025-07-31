from flask import Flask, render_template, request
import pandas as pd
from predictions import predict_next_numbers, evaluate_accuracy
import json

app = Flask(__name__)

@app.route('/')
def index():
    try:
        df = pd.read_csv("ga_cash3_history_cleaned.csv")
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
        df = df.dropna(subset=["Date", "Digit1", "Digit2", "Digit3"])
        df = df.sort_values(by="Date")

        prediction = predict_next_numbers(df)
        filter_value = int(request.args.get("filter", 30))
        accuracy_data = evaluate_accuracy(df, filter_value)

        chart_data = [
            {"date": entry["date"], "accuracy": 1 if entry["match"] in ["Exact", "AnyOrder"] else 0}
            for entry in accuracy_data["history"]
        ]

        return render_template(
            "index.html",
            prediction=prediction,
            accuracy=accuracy_data,
            chart_data=json.dumps(chart_data),
            filter_value=filter_value
        )
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
