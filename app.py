from flask import Flask, render_template
import csv
from predictor import predict_next_numbers

app = Flask(__name__)

def load_history():
    with open("data/ga_cash3_history.csv") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        return list(reader)

@app.route("/")
def index():
    history = load_history()
    if not history:
        return "No data available", 500
    last = history[-1]
    predictions = predict_next_numbers(history)
    return render_template("index.html", last=last, predictions=predictions)

if __name__ == "__main__":
    app.run(debug=True)
