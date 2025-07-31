from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

# Load data
data = pd.read_csv('ga_cash3_history_cleaned.csv')

# Make sure 'Date' is a datetime type
data['Date'] = pd.to_datetime(data['Date'])

# Route for the main page
@app.route('/', methods=['GET', 'POST'])
def index():
    filter_val = request.form.get('filter') if request.method == 'POST' else 'Midday'

    valid_filters = ['Midday', 'Evening', 'All']
    if filter_val not in valid_filters:
        filter_val = 'Midday'

    # Filter data
    if filter_val != 'All':
        filtered_data = data[data['Draw Time'] == filter_val]
    else:
        filtered_data = data

    # Count occurrences of each number
    number_counts = filtered_data['Winning Numbers'].value_counts().sort_values(ascending=False)

    # Create bar chart
    bar = go.Bar(
        x=number_counts.index,
        y=number_counts.values,
        marker=dict(color='blue')
    )

    layout = go.Layout(
        title=f"Frequency of Winning Numbers ({filter_val})",
        xaxis=dict(title='Winning Number'),
        yaxis=dict(title='Frequency')
    )

    fig = go.Figure(data=[bar], layout=layout)
    chart_html = pyo.plot(fig, output_type='div')

    return render_template('index.html', chart=chart_html, filter_val=filter_val)

if __name__ == '__main__':
    app.run(debug=True)
``
