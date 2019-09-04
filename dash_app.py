#!/home/pi/projects/rpi-projects/venv/bin/python3
# coding=utf-8
from flask import Flask, send_from_directory
from functools import reduce
import tablib
import os, csv, datetime
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

#app = Flask(__name__)
FILE_FOLDER = os.path.join(os.sep, 'home', 'pi', 'log')
RESULT_FILE = 'results.csv' 

def filter_data(data):
    indices = []
    divider = 60
    for i,item in enumerate(data):
        if i<divider:
            # first 60 entrys
            bounds=slice(0,divider)
        elif i>len(data)-divider:
            # last 60 entrys
            bounds=slice(len(data)-divider, len(data))
        else:
            # 
            bounds=slice(i-divider,i+divider)
        mean = reduce(lambda x,y: int(x)+int(y), data[bounds]) / len(data[bounds])
        if int(item) < mean:
            indices.append(i)
    return indices

def get_data(results_file, index, filter=True):
    time = []
    data = []

    #tablib.Dataset()
    with open(os.path.join(FILE_FOLDER, results_file), 'rt') as file:
        csvfile = csv.reader(file)
        for row in csvfile:
            if row:
                if row[0] == "date":
                    continue
                date=row[0] + ' ' + row[1]
                time.append(datetime.datetime.strptime(date, '%d-%m-%Y %H:%M:%S'))
                data.append(row[index])

    if filter:
        indeces = filter_data(data)
        for i in reversed(indeces):
            time.pop(i)
            data.pop(i)

    return {'x': time, 'y': data, 'type': 'scatter', 'name': 'Data', 'mode': 'lines'}
    
def get_all_results():
    res = []
    results_files = [f for f in os.listdir(FILE_FOLDER) if os.path.isfile(os.path.join(FILE_FOLDER, f)) and 'results' in f]
    for f in results_files:
        # { 'label': 'week-xx-results.csv', 'value': 'Week-xx'}
        value = ' '.join(f.split('.')[0].split('-')[:2]).capitalize()
        res.append({'label': value, 'value': f})
    return res

""" FLASK/DASH SETUP """
server = Flask(__name__, static_folder='static')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(
    __name__,
    server=server,
    routes_pathname_prefix='/graph/'
)

# Dash colors
colors = {
        'background': '#111111',
        'text': '#7FDBFF'
}


""" ROUTES """
@server.route("/")
def hello():
    return "Hello World!"

@server.route("/raw_data") 
def raw_data():
    dataset = tablib.Dataset()
    with open(os.path.join(FILE_FOLDER, RESULT_FILE), 'rt') as file:
        csvfile = csv.reader(file)
        for row in csvfile:
            if row:
                dataset.append(row)
    return dataset.html

@server.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(server.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

""" Dash App """
app.title = "Home Data"

def serve_layout():
    return html.Div(style={'backgroundColor': colors['background']},  children=[
    html.H1(children='Home Control',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    dcc.Dropdown(
        id='results_files',
        options=get_all_results(),
        #placeholder="Select a Week",
        value='results.csv',
        style={
            'backgroundColor': colors['background'],
            'color': colors['text']
        }
    ),

    dcc.Graph(
        id='temp_graph',
        config={
            'staticPlot': True
        }
    ),

    dcc.Interval(
            id='interval_graph',
            interval=60*1000, # in milliseconds
            n_intervals=0
        )
])

app.layout = serve_layout

""" CALLBACKS """
"""@app.callback(
    Output('temp_graph', 'figure'),
    [Input('interval_graph', 'n_intervals'),
     Input('results_files', 'value')]
)
def update_graph(n, results_file):
    return {
        'data': [ get_data(results_file, 2, filter = True) ],
        'layout': {
            'title': 'Temperature'
        }
    }"""

@app.callback(
    Output('temp_graph', 'figure'),
    [Input('results_files', 'value'),
    Input('interval_graph', 'n_intervals')]
)
def update_figure(results_file, n):
    if results_file:
        return {
            'data': [ get_data(results_file, 2, filter = False) ],
            'layout': {
                'title': 'Temperature',
                'backgroundColor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                }
            }
        }
    else:
        return {
            'data': []
        }

if __name__ == '__main__':
    print("Start Server")
    app.run_server(debug=True, port=5000, host='0.0.0.0')
