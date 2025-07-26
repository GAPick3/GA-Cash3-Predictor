from flask import Flask, render_template, request
import csv
from predictor import predict_next_numbers

app = Flask(__name__)

# Load draw history from CSV
def load_history():
    history = []
    try:
        with open("data/ga_cash3_history.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                history.append(row)
    except FileNotFoundError:
        print("⚠️ Warning: history file not found.")
    return history

@app.route("/", methods=["GET", "POST"])
def index():
    history = load_history()
    predictions = []

    if history:
        if request.method == "POST":
            draw_time = request.form.get("draw_time")
            if draw_time:
                predictions = predict_next_numbers(history, draw_time)
    else:
        predictions = ["Error: No history data loaded."]

    return render_template("index.html", predictions=predictions)

if __name__ == "__main__":
    app.run(debug=True)
