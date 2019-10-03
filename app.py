#!/usr/bin/env python3
#!coding=utf-8

import os
import pandas
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import scipy.signal as signal
import sql_data
from dash.dependencies import Input, Output
from flask import Flask


GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 60000*5)
COLORS = {
    'foreground': '#123456',
    'background': '#111111',
}

def layout_temp():
    return html.Div(
        [
            # curent temperature
            html.Div(
                id="current-temp",
                className="temp__current",
            ),
            dcc.Interval(
                id="current-temp-interval",
                interval=int(GRAPH_INTERVAL),
                n_intervals=0,
            ),
            html.Div(
                [
                    html.H6("Last 24 hours", className="temp__day__title"),
                    dcc.Graph(
                        id="day-temp-graph",
                        config={
                            'staticPlot': True
                        },
                        className="graph",
                    ),
                    dcc.Interval(
                        id="day-temp-update",
                        interval=int(GRAPH_INTERVAL),
                        n_intervals=0,
                    ),
                ],
                className="three-quater column temp__day",
            )
        ],
        className="app__temp",
    )

""" FLASK SETUP """
SERVER = Flask(__name__, static_folder='static')

APP = dash.Dash(
    __name__,
    server=SERVER,
    routes_pathname_prefix='/graph/'
)
""" Dash App """
APP.title = "Home Data"
APP.config['suppress_callback_exceptions'] = True

APP.layout = html.Div(
    [
        # header
        html.Div(
            [
                html.H2("HOME CONTROL DASHBOARD", className="app__header__title")
            ],
            className="app__header"
        ),
        dcc.Tabs(
            id="main-tabs",
            value="temp-tab",
            parent_className='custom__main__tabs',
            className='custom__main__tabs__container',
            children=[
                dcc.Tab(
                    label="General",
                    value="general-tab",
                    className='custom__main__tab',
                    selected_className='custom__main__tab____selected',
                ),
                dcc.Tab(
                    label="Temperature",
                    value="temp-tab",
                    className='custom__main__tab',
                    selected_className='custom__main__tab____selected',
                ),
            ]
        ),
        html.Div(
            id="main-tabs-content",
            className="app__tab__content"
        ),
    ],
    className="app__container",
)

@APP.callback(Output('main-tabs-content', 'children'),
                [Input('main-tabs', 'value')])
def render_content(tab):
    if tab == 'general-tab':
        layout = html.P("No Layout defined.")#layout_general()
    elif tab == 'temp-tab':
        layout = layout_temp()
    return layout

@APP.callback(Output('current-temp', 'children'),
                [Input('current-temp-interval', 'n_intervals')])
def update_current_temp(interval):
    last_temp = sql_data.get_last_temp()
    min_temp = sql_data.get_min_temp()
    max_temp = sql_data.get_max_temp()

    temp_range = (max_temp-min_temp)/2

    return [
        html.H6("Current Temperature", className="temp__current__title"),
        html.Div(
            [
                daq.Gauge(
                    id="current-temp-gauge",
                    value=last_temp,
                    min=min_temp,
                    max=max_temp,
                    showCurrentValue=True,
                    units="°C",
                    scale={'start': min_temp, 'interval': 1, 'labelInterval': 2, 'custom': {
                        20: '20',
                    }},
                    color={
                        "gradient":True,
                        "ranges":{
                            "blue":[min_temp, min_temp+temp_range],
                            "red":[max_temp-temp_range, max_temp]
                        }
                    },
                )
            ],
            className="temp__current__gauge",
        )
    ]


@APP.callback(Output('day-temp-graph', 'figure'),
                [Input('day-temp-update', 'n_intervals')])
def update_day_temp_graph(interval):
    day_data = sql_data.get_day_temp_pandas()
    day_data = day_data.sort_values('datetime')

    # First, design the Buterworth filter
    filter_order  = 2    # Filter order
    cutoff_freq = 0.2 # Cutoff frequency
    B, A = signal.butter(filter_order, cutoff_freq, output='ba')

    # Second, apply the filter
    tempf = signal.filtfilt(B,A, day_data['temperature'])

    return {
        'data': [
            {
                'x': day_data['datetime'],
                'y': tempf,
                'type': 'scatter',
                'name': 'Data',
                'mode': 'lines'
            },
        ],
        
        'layout': 
        {
            'backgroundColor': COLORS['background'],
            'paper_bgcolor': COLORS['background'],
            'plot_bgcolor': COLORS['background'],
            'font': {
                'color': COLORS['foreground']
            },
            'margin': {'l': 30, 'b': 30, 'r': 10, 't': 10},
            'height': '250',
        }
    }

if __name__ == "__main__":
    APP.run_server(debug=True, port=5002, host='0.0.0.0')
