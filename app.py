#!/usr/bin/env python3
#!coding=utf-8

import os
from datetime import datetime
import pandas
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import scipy.signal as signal
from flask import Flask

import pi_data
import sql_data


GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 60000)
STATS_INTERVAL = os.environ.get("STATS_INTERVAL", 5000)
COLORS = {
    'foreground': '#123456',
    'background': '#111111',
    'light-background': '#222222',
}
EMPTY_GRAPH = {
    'data': [ { 'x': [], 'y': [], }, ],
    'layout': 
    {
        'backgroundColor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background'],
        'font': {
            'color': COLORS['foreground']
        },
        'margin': {'l': 30, 'b': 30, 'r': 10, 't': 30},
        #'width': '100%',
        'height': '250',
    }
}

def app_layout():
    return html.Div(
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
                    dcc.Tab(
                        label="MQTT",
                        value="mqtt-tab",
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

def layout_temp():
    return html.Div(
        [
            html.Div(
                [
                    # curent temperature
                    html.Div(
                        id="current-temp",
                        className="temp__current",
                    ),
                    html.Div(
                        [
                            html.H6("Last 24 hours", className="temp__day__title title__center"),
                            dcc.Graph(
                                id="day-temp-graph",
                                figure=EMPTY_GRAPH,
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
                        className="temp__day",
                    )
                ],
                className="temp__curr__day",
            ),
            html.Div(
                [
                    html.H6("History", id="temp-hist-item", className="title__center"),
                    dcc.DatePickerRange(
                        id="temp-history-date-picker",
                        start_date_placeholder_text="Start Period",
                        end_date_placeholder_text="End Period",
                        #minimum_nights=1,
                        display_format='DD MM Y',
                        month_format='MM YYYY',
                        day_size=35,
                        first_day_of_week=1,
                        persistence=True,
                        persistence_type='session',
                        updatemode='bothdates',
                        with_full_screen_portal=True,
                        className="temp__hist__item",
                    ),
                    dcc.Loading(id="loading-1", children=[
                        dcc.Graph(
                            id="temp-history-graph",
                            figure=EMPTY_GRAPH,
                            config={
                                        'staticPlot': False,
                                        'showSendToCloud': False,
                                        'showLink': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'hoverClosestCartesian', 'hoverCompareCartesian', 'zoom3d', 'pan3d', 'orbitRotation', 'tableRotation', 'handleDrag3d', 'resetCameraDefault3d', 'resetCameraLastSave3d', 'hoverClosest3d; (Geo) zoomInGeo', 'zoomOutGeo', 'resetGeo', 'hoverClosestGeo', 'hoverClosestGl2d', 'hoverClosestPie', 'toggleSpikelines', 'toImage'],
                                    },
                            className="temp__hist__item graph",
                        )
                    ], type="default"),
                ],
                className="temp__hist"
            ),
        ],
        className="app__temp",
    )

def layout_general():
    return html.Div(
        [
            html.H4("Raspberry Pi Stats:"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6("CPU:"),
                                    html.Div(
                                        id="cpu-stats",
                                        className="general__stats__gauge",
                                    ),
                                ],
                                className="general__stats__cpu",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H6("RAM:"),
                                            html.Div(
                                                id="ram-stats",
                                                className="general__stats__item",
                                            ),
                                        ],
                                        id="ram-container",
                                        className="general__stats__item",
                                    ),
                                    html.Div(
                                        [
                                            html.H6("Disk:"),
                                            html.Div(
                                                id="disk-stats",
                                            ),
                                        ],
                                        id="disk-container",
                                        className="general__stats__item",
                                    ),
                                ],
                                className="general__stats__storage",
                            ),
                            
                        ],
                        className="general__stats__items",
                    ),
                    dcc.Interval(
                                id="general-stats-update",
                                interval=int(STATS_INTERVAL),
                                n_intervals=0,
                    ),
                ],
                className="general__stats",
            ),
            html.H4("Raspberry Pi Service Data:"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H6("Dashboard:"),
                            html.Div(
                                id="dashbaord-states",
                                className="general__services__states"
                            ),
                            dcc.Interval(
                                id="dashboard-interval",
                                interval=int(GRAPH_INTERVAL),
                                n_intervals=0,
                            ),
                            
                        ],
                        className="general__service__item"
                    ),
                    html.Div(
                        [
                            html.H6("Datalogger:"),
                            html.Div(
                                id="datalogger-states",
                                className="general__services__states"
                            ),
                            dcc.Interval(
                                id="datalogger-interval",
                                interval=int(GRAPH_INTERVAL),
                                n_intervals=0,
                            ),
                            
                        ],
                        className="general__service__item"
                    ),
                    html.Div(
                        [
                            html.H6("MQTT:"),
                            html.Div(
                                id="mqtt-states",
                                className="general__services__states"
                            ),
                            dcc.Interval(
                                id="mqtt-interval",
                                interval=int(GRAPH_INTERVAL),
                                n_intervals=0,
                            ),
                            
                        ],
                        className="general__service__item"
                    ),
                ],
                className="general__services",
            ),
        ],
        className="app__general",
    )

def layout_mqtt():
    data = sql_data.get_mqtt_messages()
    print(data)
    return html.Div(
        [
            html.H4("All MQTT Messages:"),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in data.columns],
                data=data.to_dict('records'),

                style_as_list_view=True,
                style_header={
                    'backgroundColor': COLORS['light-background'],
                    'fontWeight': 'bold'
                },
                style_cell={
                    'padding': '5px',
                    'textAlign': 'center',
                    'backgroundColor': COLORS['background'],
                },
            ),
        ],
        className="app__mqtt",
    )

def get_states(sub_color, active_color, load_color):
    return [
        daq.Indicator(
            label="Service Running",
            color=sub_color,
            className="general__services__state",
        ),
        daq.Indicator(
            label="Service State",
            color=active_color,
            className="general__services__state",
        ),
        daq.Indicator(
            label="State Config File",
            color=load_color,
            className="general__services__state",
        ),
    ]

def get_state_colors(data):
    if data['LoadState'] == 'loaded':
        load_color = "green"
    elif data['LoadState'] == 'masked':
        load_color = "yellow"
    else:
        load_color = "red"

    if data['SubState'] == 'running':
        sub_color = "green"
    else:
        sub_color = "red"
    
    if data['ActiveState'] == 'active':
        active_color = "green"
    elif data['ActiveState'] in ['reloading', 'activating', 'deactivating']:
        active_color = "yellow"
    elif data['ActiveState'] == 'inactive':
        active_color = "orange"
    else:
        active_color = "red"

    return (sub_color, active_color, load_color)

# FLASK SETUP
SERVER = Flask(__name__, static_folder='static')

# DASH SETUP
APP = dash.Dash(
    __name__,
    server=SERVER,
    routes_pathname_prefix='/graph/'
)
APP.title = "Home Data"
APP.config['suppress_callback_exceptions'] = True

APP.layout = app_layout



@APP.callback(Output('main-tabs-content', 'children'),
              [Input('main-tabs', 'value')])
def render_content(tab):
    if tab == 'general-tab':
        layout = layout_general()
    elif tab == 'temp-tab':
        layout = layout_temp()
    elif tab == 'mqtt-tab':
        layout = layout_mqtt()
    return layout


@APP.callback(Output('current-temp', 'children'),
              [Input('day-temp-update', 'n_intervals')])
def update_current_temp(interval):
    last_temp = sql_data.get_last_temp()
    min_temp = sql_data.get_min_temp()
    max_temp = sql_data.get_max_temp()

    temp_range = (max_temp-min_temp)/2

    return [
        html.H6("Current Temperature", className="temp__current__title title__center"),
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

    # Design of Buterworth filter
    filter_order  = 2    # Filter order
    cutoff_freq = 0.2 # Cutoff frequency
    B, A = signal.butter(filter_order, cutoff_freq, output='ba')

    # Apply filter
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
            'autosize': True,
            'backgroundColor': COLORS['background'],
            'paper_bgcolor': COLORS['background'],
            'plot_bgcolor': COLORS['background'],
            'font': {
                'color': COLORS['foreground']
            },
            'margin': {'l': 30, 'b': 30, 'r': 10, 't': 10},
            #'width': '100%',
            'height': '250',
        }
    }


@APP.callback(
    Output('temp-history-graph', 'figure'),
    [Input('temp-history-date-picker', 'start_date'),
     Input('temp-history-date-picker', 'end_date')])
def update_temp_history_graph(start_date, end_date):
    if start_date is not None and end_date is not None:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        data = sql_data.get_temp_history(start_date, end_date)

        if data.empty:
            return EMPTY_GRAPH

        # Design of Buterworth filter
        filter_order  = 2    # Filter order
        cutoff_freq = 0.2 # Cutoff frequency
        B, A = signal.butter(filter_order, cutoff_freq, output='ba')

        # Apply filter
        tempf = signal.filtfilt(B,A, data['temperature'], axis=0)

        return {
            'data': [
                {
                    'x': data['datetime'],
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
                #'width': '100%',
                'height': '500',
            }
        }
    else:
        return EMPTY_GRAPH


@APP.callback(Output('dashbaord-states', 'children'),
              [Input('dashboard-interval', 'n_intervals')])
def update_dashboard_service(interval):
    data = pi_data.get_service_data("dashboard")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('datalogger-states', 'children'),
              [Input('datalogger-interval', 'n_intervals')])
def update_datalogger_service(interval):
    data = pi_data.get_service_data("data-logger")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('mqtt-states', 'children'),
              [Input('mqtt-interval', 'n_intervals')])
def update_mqtt_service(interval):
    data = pi_data.get_service_data("mqtthandler")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('cpu-stats', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def cpu_state(interval):
    cpu_percent = pi_data.get_cpu_percent()
    return daq.Gauge(
        id="cpu-gauge",
        value=cpu_percent,
        min=0,
        max=100,
        showCurrentValue=True,
        units="%",
        scale={'start': 0, 'interval': 5, 'labelInterval': 25},
        color={
            "gradient":True,
            "ranges":{
                "green":[0,33],
                "yellow":[33,66],
                "red":[66,100]
            }
        },
        size=200,
    )


@APP.callback(Output('ram-stats', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def ram_state(interval):
    ram = pi_data.get_ram_data()
    return daq.GraduatedBar(
        max=100,
        value=ram['percent'],
        showCurrentValue=True,
    )


@APP.callback(Output('disk-stats', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def disk_state(interval):
    disk = pi_data.get_disk_data()
    return daq.GraduatedBar(
        max=100,
        value=disk['percent'],
        showCurrentValue=True,
    )

if __name__ == "__main__":
    APP.run_server(debug=True, port=5002, host='0.0.0.0')
