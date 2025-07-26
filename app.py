# app.py

from flask import Flask, render_template
from predictor import predict_next_numbers
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    df = pd.read_csv('data/ga_cash3_history.csv')
    latest = df.iloc[0]
    predictions = predict_next_numbers()

    return render_template("index.html", latest=latest, predictions=predictions)

if __name__ == "__main__":
    app.run(debug=True)
