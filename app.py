from flask import Flask, render_template, request
from predictor import load_history, predict_top5

app = Flask(__name__)  # ✅ MUST be before route decorators

@app.route("/", methods=["GET", "POST"])
def index():

    predictions = None
    if request.method == 'POST':
        dtype = request.form['draw_type']
        alpha = float(request.form['alpha'])
        beta = float(request.form['beta'])
        gamma = float(request.form['gamma'])
        history = load_history('data/ga_cash3_history.csv', dtype)
    if not history:
        return "No data available. Please check the scraper."

        last = history[-1]
else:
    last = None
        predictions = predict_top5(history, alpha, beta, gamma)
    return render_template('index.html', preds=predictions)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
