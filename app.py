from flask import Flask, render_template
from predictor import predict_next_numbers
import pandas as pd
from datetime import datetime

app = Flask(__name__)

HISTORY_PATH = 'data/ga_cash3_history.csv'
PREDICTION_LOG_PATH = 'data/prediction_log.csv'

@app.route('/')
def index():
    # Load latest result
    df = pd.read_csv(HISTORY_PATH)
    latest_draw = df.iloc[-1]
    draw_date = latest_draw['Date']
    draw_time = latest_draw['DrawTime']
    winning_number = latest_draw['Winning Numbers']

    # Generate prediction
    prediction = predict_next_numbers(df)

    # Log prediction
    log_prediction(prediction, draw_date, draw_time)

    # Load last 10 predictions
    if os.path.exists(PREDICTION_LOG_PATH):
        prediction_log = pd.read_csv(PREDICTION_LOG_PATH).tail(10).iloc[::-1]
    else:
        prediction_log = pd.DataFrame(columns=['Date', 'DrawTime', 'Prediction'])

    return render_template('index.html',
                           latest_date=draw_date,
                           latest_time=draw_time,
                           winning_number=winning_number,
                           prediction=prediction,
                           prediction_log=prediction_log)

def log_prediction(prediction, date, draw_time):
    df_log = pd.DataFrame([{
        'Date': date,
        'DrawTime': draw_time,
        'Prediction': prediction
    }])

    if os.path.exists(PREDICTION_LOG_PATH):
        df_log.to_csv(PREDICTION_LOG_PATH, mode='a', header=False, index=False)
    else:
        df_log.to_csv(PREDICTION_LOG_PATH, index=False)

if __name__ == '__main__':
    app.run(debug=True)
