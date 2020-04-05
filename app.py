#!/usr/bin/env python3

import os
import logging
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import dash_table
# import pandas as pd
# import numpy as np
import scipy.signal as signal
import paho.mqtt.client as mqtt
import plotly.graph_objects as go

from math import ceil
from collections import deque
from datetime import datetime
from flask import Flask
from dash.dependencies import Input, Output

import pi_data
import sql_data
import mqtt_live

logger = logging.getLogger(__name__)

B_MQTT_BUTTONS = True
GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 60000)
STATS_INTERVAL = os.environ.get("STATS_INTERVAL", 5000)
MQTT_CLIENT = mqtt.Client("Dashboard")
MQTT_CLIENT.connected_flag = False
MQTT_CLIENT.enable_logger()
QUEUE = deque(maxlen=20)
N_BUTTON_HIST = 0
COLORS = {
    'foreground': '#123456',
    'main': '#7FDBFF',  # 4491ed',
    'background': '#111111',
    'light-background': '#222222',
    'red': 'red',
    'green': 'green',
    'colorway': [
        '#fc5c65',
        '#45aaf2',
        '#fd9644',
        '#4b7bec',
        '#fed330',
        '#a55eea',
        '#26de81',
        '#d1d8e0',
        '#2bcbba',
        '#778ca3',
        '#eb3b5a',
        '#2d98da',
        '#fa8231',
        '#3867d6',
        '#f7b731',
        '#8854d0',
        '#20bf6b',
        '#a5b1c2',
        '#0fb9b1',
        '#4b6584',
    ]
}
EMPTY_GRAPH = {
    'data': [{'x': [], 'y': [], }, ],
    'layout':
    {
        'backgroundColor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background'],
        'font': {
            'color': COLORS['foreground']
        },
        'margin': {'l': 30, 'b': 30, 'r': 10, 't': 30},
        # 'width': '100%',
        'height': '250',
    }
}
UNITS = {
    'temperature': '°C',
    'pressure': 'Pa',
    'humidity': '%',
    'altitude': 'm',
    'brightness': 'lx',
}


def app_layout():
    return html.Div(
        [
            # store site's settings
            # dcc.Store(id='local', storage_type='local'),
            # header
            dcc.Tabs(
                id="main-tabs",
                value="data-tab",
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
                        label="Data",
                        value="data-tab",
                        className='custom__main__tab',
                        selected_className='custom__main__tab____selected',
                    ),
                    dcc.Tab(
                        label="MQTT",
                        value="mqtt-tab",
                        className='custom__main__tab',
                        selected_className='custom__main__tab____selected',
                    ),
                    dcc.Tab(
                        label="Shopping",
                        value="shopping-tab",
                        className='custom__main__tab',
                        selected_className='custom__main__tab____selected',
                    ),
                ]
            ),
            # html.Div(
            #     [
            #         html.H4("HOME CONTROL DASHBOARD", className="app__header__title")
            #     ],
            #     className="app__header"
            # ),
            html.Div(
                id="main-tabs-content",
                className="app__tab__content"
            ),
        ],
        className="app__container",
    )


def layout_data():
    return html.Div(
        [
            dcc.Tabs(
                id="data-main-tabs",
                value="data-overview-tab",
                parent_className='custom__main__tabs',
                className='custom__main__tabs__container',
                children=[
                    dcc.Tab(
                        label="Overview",
                        value="data-overview-tab",
                        className='custom__main__sub__tab',
                        selected_className='custom__main__sub__tab____selected',
                    ),
                    dcc.Tab(
                        label="Graph",
                        value="data-graph-tab",
                        className='custom__main__sub__tab',
                        selected_className='custom__main__sub__tab____selected',
                    ),
                    # dcc.Tab(
                    #     label="Settings",
                    #     value="data-settings-tab",
                    #     className='custom__main__sub__tab',
                    #     selected_className='custom__main__sub__tab____selected',
                    # ),
                ]
            ),
            html.Div(
                id="data-tabs-content",
                className="app__tab__content"
            ),
        ],
    )


def layout_data_overview():
    return html.Div(
        [
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className="six column",
                        children=[
                            html.H6("Choose displayed data:")
                        ]
                    ),
                    html.Div(
                        className="six column",
                        children=[
                            dcc.Checklist(
                                id="data-overview-values",
                                options=[
                                    {'label': 'Temperature', 'value': 'temperature'},
                                    {'label': 'Humidity', 'value': 'humidity'},
                                    {'label': 'Pressure', 'value': 'pressure'},
                                    {'label': 'Altitude', 'value': 'altitude', 'disabled': True},
                                    {'label': 'Brightness', 'value': 'brightness'},
                                ],
                                value=['temperature', 'humidity', 'pressure'],
                                labelStyle={'display': 'inline-block'},
                                persistence_type='memory',
                            ),
                        ]
                    )
                ]
            ),
            #html.Div(
            #    className='row',
            #    id="current-data",
            #),
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className="twelve column",
                        children=[
                            html.H6("Last 24 hours", className="data__overview__day__title title__center"),
                        ],
                    ),
                    html.Div(
                        className="twelve column",
                        children=[
                            dcc.Graph(
                                id="day-data-graph",
                                figure=EMPTY_GRAPH,
                                config={
                                    'staticPlot': True
                                },
                                className="graph",
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Interval(
                id="data-overview-update",
                interval=int(GRAPH_INTERVAL),
                n_intervals=0,
            ),
        ],
        className="container" #  data__overview",
    )


def layout_data_graph():
    return html.Div(
        [
            dcc.DatePickerRange(
                id="data-history-date-picker",
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text="End Period",
                # minimum_nights=1,
                display_format='DD MM Y',
                month_format='MM YYYY',
                day_size=35,
                first_day_of_week=1,
                persistence=True,
                persistence_type='session',
                updatemode='bothdates',
                with_full_screen_portal=True,
                className="data__hist__item",
            ),
            dcc.Loading(id="loading-1", color=COLORS['main'], children=[
                dcc.Graph(
                    id="data-history-graph",
                    figure=EMPTY_GRAPH,
                    config={
                                'staticPlot': False,
                                'showSendToCloud': False,
                                'showLink': False,
                                'displaylogo': False,
                                'modeBarButtonsToRemove':
                                [
                                    'sendDataToCloud',
                                    'hoverClosestCartesian',
                                    'hoverCompareCartesian',
                                    'zoom3d',
                                    'pan3d',
                                    'orbitRotation',
                                    'tableRotation',
                                    'handleDrag3d',
                                    'resetCameraDefault3d',
                                    'resetCameraLastSave3d',
                                    'hoverClosest3d; (Geo) zoomInGeo',
                                    'zoomOutGeo',
                                    'resetGeo',
                                    'hoverClosestGeo',
                                    'hoverClosestGl2d',
                                    'hoverClosestPie',
                                    'toggleSpikelines',
                                    'toImage'
                                ],
                            },
                    className="data__hist__item graph",
                )
            ], type="default"),
        ],
        className="temp__hist"
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
                            html.H6("MQTT Handler:"),
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
                            html.H6("Probemon:"),
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
    return html.Div(
        [
            dcc.Tabs(
                id="mqtt-main-tabs",
                value="mqtt-messages-tab",
                parent_className='custom__main__tabs',
                className='custom__main__tabs__container',
                children=[
                    dcc.Tab(
                        label="Messages",
                        value="mqtt-messages-tab",
                        className='custom__main__sub__tab',
                        selected_className='custom__main__sub__tab____selected',
                    ),
                    dcc.Tab(
                        label="Live",
                        value="mqtt-live-tab",
                        className='custom__main__sub__tab',
                        selected_className='custom__main__sub__tab____selected',
                    ),
                ]
            ),
            html.Div(
                id="mqtt-tabs-content",
                className="app__tab__content"
            ),
        ],
    )


def layout_mqtt_messages():
    topics = sql_data.get_mqtt_topics()
    return html.Div(
        [
            html.Div(
                children=[
                    html.H6("Select topics:"),
                    dcc.Checklist(
                        id="mqtt-select-topics",
                        value=['tablet/shield/battery'] if 'tablet/shield/battery' in topics else [],
                        labelStyle={'display': 'inline-block'},
                        options=[{'label': topic, 'value': topic} for topic in sql_data.get_mqtt_topics()],
                        className="mqtt__topic__select",
                    ),
                    html.H6("Select number of entries:"),
                    dcc.Input(
                        id='mqtt-select-num-msgs',
                        type='number',
                        value=1000,
                        min=1,
                        max=99999,
                        debounce=True,
                    )
                ],
                className='mqtt__settings__panel',
            ),
            dcc.Loading(id="loading-1", color=COLORS['main'], children=[
                dash_table.DataTable(
                    id='table',
                    columns=[
                        {"name": 'Date/Time', "id": 'datetime'},
                        {"name": 'Topic', "id": 'topic'},
                        {"name": 'Payload', "id": 'payload'},
                    ],
                    data=[],  # data.to_dict('records'),

                    page_action="native",
                    page_current=0,
                    page_size=20,
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
            ], type="default"),
        ],
        className="mqtt__messages",
    )


def layout_mqtt_live():
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        [
                            html.Datalist(
                                id='mqtt-topic-recent',
                                children=[html.Option(value=val) for val in sql_data.get_mqtt_topics()],
                            ),
                            dcc.Input(
                                id='mqtt-topic-input',
                                # debounce=True,
                                list='mqtt-topic-recent',
                                placeholder="Topic...",
                                # persistence=True,
                                # persistence_type='session',
                                style={
                                    'backgroundColor': COLORS['light-background'],
                                    'color': COLORS['main'],
                                    'border': f"2px solid {COLORS['main']}",
                                    'border-radius': '4px',
                                    'padding': '6px 10px',
                                },
                            ),
                            html.Button('Subscribe', id='mqtt-live-subscribe'),
                            html.Div(id='mqtt-live-sub-status'),
                        ],
                        className='mqtt__live__input'
                    ),
                    html.Div(
                        [
                            html.Button(
                                'Start',
                                id='mqtt-live-start',
                                disabled=False,
                                className='start__stop__button',
                            ),
                            html.Button('Stop', id='mqtt-live-stop', disabled=True, className='start__stop__button'),
                        ],
                        className='mqtt__live__start__stop__buttons'
                    )
                ],
                className="mqtt__live__control",
            ),
            dcc.Interval(id='mqtt-live-interval', interval=500),
            dash_table.DataTable(
                id='live-table',
                columns=[
                    {"name": 'Date', "id": 'date', 'selectable': False},
                    {"name": 'Time', "id": 'time'},
                    {"name": 'Topic', "id": 'topic'},
                    {"name": 'Payload', "id": 'payload'},
                    {"name": 'qos', "id": 'qos'},
                ],
                data=[],  # data.to_dict('records'),
                editable=False,
                page_action="native",
                page_current=0,
                page_size=20,
                style_as_list_view=True,
                is_focused=False,
                style_header={
                    'backgroundColor': COLORS['light-background'],
                    'fontWeight': 'bold'
                },
                style_cell={
                    'padding': '5px',
                    'textAlign': 'center',
                    'backgroundColor': COLORS['background'],
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': COLORS['light-background']
                    }
                ],
            ),
        ],
        className="mqtt__live",
    )


def layout_shopping():
    return html.Div([
        dcc.Tabs(
            id="shopping-main-tabs",
            value="shopping-overview-tab",
            parent_className='custom__main__tabs',
            className='custom__main__tabs__container',
            children=[
                dcc.Tab(
                    label="Overview",
                    value="shopping-overview-tab",
                    className='custom__main__sub__tab',
                    selected_className='custom__main__sub__tab____selected',
                ),
                dcc.Tab(
                    label="Add Shopping List",
                    value="shopping-add-tab",
                    className='custom__main__sub__tab',
                    selected_className='custom__main__sub__tab____selected',
                ),
            ]
        ),
        dcc.Loading(id="loading-2", color=COLORS['main'], children=[
            html.Div(
                id="shopping-tabs-content",
                className="app__tab__content"
            ),
        ], type="default"),
    ])


def layout_shopping_overview():
    df_days = sql_data.get_unique_shopping_days()
    shops = sql_data.get_unique_shopping_shops()
    shops = shops.sort_values('Shop')

    data = []
    for shop in shops.Shop:
        expense = sql_data.get_shopping_expenses_per_shop(shop)
        df_days = df_days.join(expense)
        data.append(go.Bar(
            name=shop,
            x=df_days.index,
            y=df_days[shop],
            hovertemplate="%{x|%d.%m.%Y} : %{y:.2f}€",
            marker={
                'line': {
                    'width': 0,
                    'color': COLORS['background'],
                }
            }
        ))

    fig = go.Figure(data=data)
    fig.update_layout(
        barmode='stack',
        autosize=True,
        legend={
            'orientation': 'h',
        },
        font={
            'color': COLORS['main'],
        },
        colorway=COLORS['colorway'],
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        coloraxis={
            'colorbar': {
                'outlinewidth': 0,
                'bordercolor': COLORS['background'],
                'bgcolor': COLORS['background'],
            },
        },
    )
    return dcc.Graph(
        id="shopping-overview-graph",
        figure=fig,
        clear_on_unhover=True,
        config={
            'staticPlot': False,
        },
        className="shopping__daily_graph graph",
    )


def layout_shopping_add():
    return "no"


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
    if data:
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
    else:
        load_color = "red"
        sub_color = "red"
        active_color = "red"
    return (sub_color, active_color, load_color)


# FLASK SETUP
SERVER = Flask(__name__, static_folder='static')

# DASH SETUP
APP = dash.Dash(
    __name__,
    server=SERVER,
    # routes_pathname_prefix='/graph/'
)
APP.title = "Home Data"
APP.config['suppress_callback_exceptions'] = True

APP.layout = app_layout


@APP.callback(Output('main-tabs-content', 'children'),
              [Input('main-tabs', 'value')])
def render_main_content(tab):
    if tab == 'general-tab':
        layout = layout_general()
    elif tab == 'data-tab':
        layout = layout_data()
    elif tab == 'mqtt-tab':
        layout = layout_mqtt()
    else:
        layout = layout_shopping()
    return layout


@APP.callback(Output('data-tabs-content', 'children'),
              [Input('data-main-tabs', 'value')])
def render_data_content(tab):
    if tab == 'data-overview-tab':
        layout = layout_data_overview()
    elif tab == 'data-graph-tab':
        layout = layout_data_graph()
    elif tab == 'data-settings-tab':
        layout = html.Div("Settings")
    return layout


@APP.callback(Output('mqtt-tabs-content', 'children'),
              [Input('mqtt-main-tabs', 'value')])
def render_mqtt_content(tab):
    if tab == 'mqtt-messages-tab':
        layout = layout_mqtt_messages()
    elif tab == 'mqtt-live-tab':
        layout = layout_mqtt_live()
    elif tab == 'mqtt-settings-tab':
        layout = html.Div("Settings")
    return layout


@APP.callback(Output('shopping-tabs-content', 'children'),
              [Input('shopping-main-tabs', 'value')])
def render_shopping_content(tab):
    if tab == 'shopping-overview-tab':
        layout = layout_shopping_overview()
    elif tab == 'shopping-add-tab':
        layout = layout_shopping_add()
    return layout


@APP.callback(Output('current-data', 'children'),
              [Input('data-overview-update', 'n_intervals'),
               Input('data-overview-values', 'value')])
def update_current_data(interval, overview_values):
    gauges = []
    for value in overview_values:
        last = sql_data.get_last_value(value)
        min_val = round(sql_data.get_min_value(value))
        max_val = ceil(sql_data.get_max_value(value))
        step = round((max_val - min_val) / 3)
        if value in UNITS.keys():
            unit = UNITS[value]
        else:
            unit = ''

        gauges.append(html.Div(
            [
                html.H6(f"Current {value.capitalize()}", className="temp__current__title title__center"),
                html.Div(
                    [
                        daq.Gauge(
                            id="current-temp-gauge",
                            value=last,
                            min=min_val,
                            max=max_val,
                            showCurrentValue=True,
                            units=unit,
                            # s cale={'start': min_val, 'interval': 1, 'labelInterval': 2},
                            color={
                                "gradient": True,
                                "ranges": {
                                    "blue": [min_val, min_val + step],
                                    "green": [min_val + step, max_val - step],
                                    "red": [max_val - step, max_val]
                                }
                            },
                        )
                    ],
                    className="temp__current__gauge",
                )
            ],
            className="overview__current__gauges"
        ))
    return gauges


@APP.callback(Output('day-data-graph', 'figure'),
              [Input('data-overview-update', 'n_intervals'),
               Input('data-overview-values', 'value')])
def update_day_graph(interval, overview_values):
    day_data = sql_data.get_day_temp()
    day_data = day_data.sort_values('datetime')

    # Design of Buterworth filter
    filter_order = 2    # Filter order
    cutoff_freq = 0.2   # Cutoff frequency
    B, A = signal.butter(filter_order, cutoff_freq, output='ba')

    # Apply filter
    tempf = signal.filtfilt(B, A, day_data['temperature'])

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
            # 'width': '100%',
            'height': '380',
        }
    }


@APP.callback(
    Output('data-history-graph', 'figure'),
    [Input('data-history-date-picker', 'start_date'),
     Input('data-history-date-picker', 'end_date')])
def update_history_graph(start_date, end_date):
    if start_date is not None and end_date is not None:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        data = sql_data.get_temp_history(start_date, end_date)

        if data.empty:
            return EMPTY_GRAPH

        # Design of Buterworth filter
        filter_order = 2    # Filter order
        cutoff_freq = 0.2   # Cutoff frequency
        B, A = signal.butter(filter_order, cutoff_freq, output='ba')

        # Apply filter
        tempf = signal.filtfilt(B, A, data['temperature'], axis=0)

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
                # 'width': '100%',
                'height': '500',
            }
        }
    else:
        return EMPTY_GRAPH


@APP.callback(Output('table', 'data'),
              [Input('mqtt-select-topics', 'value'),
               Input('mqtt-select-num-msgs', 'value')])
def get_table_data(selected_topics, limit):
    if selected_topics and limit:
        logger.debug(f"MQTT Messages callback. Topics: {selected_topics}, limit: {limit}.")
        data = sql_data.get_mqtt_messages_by_topic(selected_topics, limit)
        return data.to_dict('records')
    else:
        return []


@APP.callback(Output('mqtt-topic-input', 'style'),
              [Input('mqtt-topic-input', 'value')])
def sanitize_topic(topic):
    if topic:
        if mqtt_live.sanitize_topic(topic):
            style = {
                'backgroundColor': COLORS['light-background'],
                'color': COLORS['main'],
                'border': f"2px solid {COLORS['green']}",
                'border-radius': '4px',
                'padding': '6px 10px',
            }
        else:
            style = {
                'backgroundColor': COLORS['light-background'],
                'color': COLORS['main'],
                'border': f"2px solid {COLORS['red']}",
                'border-radius': '4px',
                'padding': '6px 10px',
            }
    else:
        style = {
            'backgroundColor': COLORS['light-background'],
            'color': COLORS['main'],
            'border': f"2px solid {COLORS['main']}",
            'border-radius': '4px',
            'padding': '6px 10px',
        }
    return style


@APP.callback(Output('mqtt-live-sub-status', 'children'),
              [Input('mqtt-live-subscribe', 'n_clicks'),
               Input('mqtt-topic-input', 'value')])
def subscribe_mqtt_topic(n_clicks, topic):
    global MQTT_CLIENT, N_BUTTON_HIST

    ctx = dash.callback_context
    if not ctx.triggered or not topic or not n_clicks or N_BUTTON_HIST == n_clicks:
        return ""
    elif not mqtt_live.sanitize_topic(topic):
        N_BUTTON_HIST = n_clicks
        return "Invalid Topic!"
    elif not MQTT_CLIENT.connected_flag:
        N_BUTTON_HIST = n_clicks
        return "Press Start first!"
    else:
        N_BUTTON_HIST = n_clicks
        MQTT_CLIENT.subscribe(topic)
        return "Subscribed!"


@APP.callback([Output('mqtt-live-start', 'disabled'),
               Output('mqtt-live-stop', 'disabled')],
              [Input('mqtt-live-start', 'n_clicks'),
               Input('mqtt-live-stop', 'n_clicks')])
def toggle_buttons(n_clicksb1, n_clicksb2):
    global MQTT_CLIENT
    if dash.callback_context.triggered:
        context = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
        if context == 'mqtt-live-start':
            mqtt_live.mqtt_connect_async(MQTT_CLIENT, QUEUE)
            return True, False
        else:
            MQTT_CLIENT.disconnect()
            MQTT_CLIENT = mqtt.Client("Dashboard")
            MQTT_CLIENT.connected_flag = False
            MQTT_CLIENT.enable_logger()
            return False, True
    return True, False


@APP.callback(Output('live-table', 'data'),
              [Input('mqtt-live-interval', 'n_intervals')])
def render_mqtt_live(interval):
    return list(QUEUE)


@APP.callback(Output('dashbaord-states', 'children'),
              [Input('dashboard-interval', 'n_intervals')])
def update_dashboard_service(interval):
    data = pi_data.get_service_data("dashboard")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('datalogger-states', 'children'),
              [Input('datalogger-interval', 'n_intervals')])
def update_datalogger_service(interval):
    data = pi_data.get_service_data("mqtthandler")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('mqtt-states', 'children'),
              [Input('mqtt-interval', 'n_intervals')])
def update_mqtt_service(interval):
    data = pi_data.get_service_data("probemon", user=False)
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
            "gradient": True,
            "ranges": {
                "green": [0, 33],
                "yellow": [33, 66],
                "red": [66, 100]
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
        className='graduated__bar',
    )


@APP.callback(Output('disk-stats', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def disk_state(interval):
    disk = pi_data.get_disk_data()
    return daq.GraduatedBar(
        max=100,
        value=disk['percent'],
        showCurrentValue=True,
        className='graduated__bar',
    )


if __name__ == "__main__":
    APP.run_server(debug=True, port=5002, host='0.0.0.0')
