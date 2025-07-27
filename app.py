from flask import Flask, render_template
from predictor import predict_next_numbers
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def index():
    try:
        df = pd.read_csv('data/ga_cash3_history.csv')
        if df.empty:
            return render_template("index.html", error="No draw data found.")
    except Exception as e:
        return render_template("index.html", error=f"Error loading data: {e}")

    latest = df.iloc[0]
    predictions = predict_next_numbers(df)
    return render_template("index.html", latest=latest, predictions=predictions)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
