# app.py
from flask import Flask, render_template
import pandas as pd
from strategy_predictor import generate_strategic_predictions

app = Flask(__name__)

data_path = "data/ga_cash3_history.csv"
prediction_log_path = "data/prediction_log.csv"


def get_latest_result():
    df = pd.read_csv(data_path)
    latest = df.iloc[0]  # Assuming most recent is first row
    return {
        "date": latest["Date"],
        "draw": latest["Draw"],
        "digits": f"{latest['Digit1']}{latest['Digit2']}{latest['Digit3']}",
        "draw_time": latest["DrawTime"]
    }


def get_prediction_log(n=10):
    try:
        df = pd.read_csv(prediction_log_path)
        return df.tail(n).to_dict(orient="records")
    except FileNotFoundError:
        return []


@app.route("/")
def index():
    latest_result = get_latest_result()
    predictions = generate_strategic_predictions()
    prediction_log = get_prediction_log()
    return render_template("index.html", result=latest_result, predictions=predictions, history=prediction_log)


if __name__ == "__main__":
    app.run(debug=True)
