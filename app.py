#!/usr/bin/env python3

import os
import logging
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd
import scipy.signal as signal
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from math import ceil
from calendar import month_name
from collections import deque
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State, ALL  # , MATCH
from dash.exceptions import PreventUpdate

import graph_helper
import pi_data
import sql_data
try:
    import mqtt_live
    ENABLE_LIVE = True
except ImportError:
    ENABLE_LIVE = False


logging.basicConfig(
    level=logging.DEBUG,
    format="%(module)s - %(levelname)s : %(message)s",
)
logger = logging.getLogger('dashboard')


B_MQTT_BUTTONS = True
GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 60000)
STATS_INTERVAL = os.environ.get("STATS_INTERVAL", 5000)
MQTT_CLIENT = mqtt.Client("Dashboard")
MQTT_CLIENT.connected_flag = False
MQTT_CLIENT.enable_logger()
QUEUE = deque(maxlen=20)
N_BUTTON_HIST = 0
N_SHOPPING_ITEMS = 15
COLORS = {
    'foreground': '#7FDBFF',  # 4491ed',
    'foreground-dark': '#123456',
    'background': '#111111',
    'background-medium': '#252525',
    'border-light': '#d6d6d6',
    'border-medium': '#333333',
    'border-dark': '#0f0f0f',
    'dark-1': '#222222',
    'dark-2': '#333333',
    'red': 'red',
    'green': 'green',
    'error': '#960c0c',
    'success': '#17960c',
    'colorway': [
        '#fc5c65',
        '#26de81',
        '#fd9644',
        '#2bcbba',
        '#a55eea',
        '#bff739',
        '#45aaf2',
        '#fed330',
        '#4b7bec',
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
            'color': COLORS['foreground-dark']
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
DIV_COLUMNS = {
    1: "twelve columns",
    2: "eight columns",
    3: "four columns",
    4: "three columns",
    5: "two columns",
}


def app_layout():
    return html.Div(
        [
            # store site's settings
            # dcc.Store(id='local', storage_type='local'),
            # header
            dcc.Store(
                id='shopping-products-store',
                storage_type='session',
            ),
            dcc.Store(
                id='shopping-shops-store',
                storage_type='session',
            ),
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
        children=[
            html.Div(
                children=[
                    html.H6("Choose display data:"),
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
                        labelStyle={'display': 'block'},
                        persistence_type='memory',
                        className='checklist',
                    )
                ],
                className='two columns settings',
            ),
            html.Div(
                children=[
                    html.Div(
                        id="current-data",
                        className='overview__current__gauges row',
                    ),
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
                                className="twelve column graph_in_column",
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
                className='ten columns data',
            )
        ],
        className='row',
    )


def layout_data_graph():
    return html.Div(
        children=[
            html.Div(
                children=[
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
                    ),
                ],
                className="two columns",
            ),
            html.Div(
                children=[
                    dcc.Loading(id="loading-1", color=COLORS['foreground'], children=[
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
                                    'hoverClosest3d',
                                    'zoomInGeo',
                                    'zoomOutGeo',
                                    'resetGeo',
                                    'hoverClosestGeo',
                                    'hoverClosestGl2d',
                                    'hoverClosestPie',
                                    'toggleSpikelines',
                                    'toImage'
                                ],
                            },
                            className="graph",
                        )
                    ], type="default"),
                ],
                className="ten columns",
            )
        ],
        className="row"  # temp__hist
    )


def layout_general():
    return html.Div(
        [
            dcc.Interval(
                id="general-stats-update",
                interval=int(STATS_INTERVAL),
                n_intervals=0,
            ),
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className='four columns',
                        children=[
                            html.H4("Raspberry Pi Stats:"),
                        ]
                    ),
                    html.Div(
                        className='eight columns',
                        children=[
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        [
                                            html.H6("CPU:"),
                                        ],
                                        className="four columns",  # general__stats__item",
                                    ),
                                    html.Div(
                                        id="cpu-stats",
                                        className="eight columns"  # general__stats__item",
                                    ),
                                ]
                            ),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        [
                                            html.H6("RAM:"),
                                        ],
                                        className="four columns",  # general__stats__item",
                                    ),
                                    html.Div(
                                        id="ram-stats",
                                        className="eight columns"  # general__stats__item",
                                    ),
                                ]
                            ),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        [
                                            html.H6("Disk:"),
                                        ],
                                        className="four columns",  # general__stats__item",
                                    ),
                                    html.Div(
                                        id="disk-stats",
                                        className="eight columns"  # general__stats__item",
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className='four columns',
                        children=[
                            html.H4("Raspberry Pi Service Data:"),
                        ]
                    ),
                    html.Div(
                        className='eight columns',
                        children=[
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className="four columns",
                                        children=[
                                            html.H6("Dashboard:"),
                                        ]
                                    ),
                                    html.Div(
                                        id="dashbaord-states",
                                        className="eight columns",
                                    ),
                                ]
                            ),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className="four columns",
                                        children=[
                                            html.H6("MQTT Handler:"),
                                        ]
                                    ),
                                    html.Div(
                                        id="datalogger-states",
                                        className="eight columns",
                                    ),
                                ]
                            ),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className="four columns",
                                        children=[
                                            html.H6("Probemon:"),
                                        ]
                                    ),
                                    html.Div(
                                        id="mqtt-states",
                                        className="eight columns",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            )
        ],
        className=""
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
    return html.Div([
        html.Div(
            className='row',
            children=[
                html.Div(
                    className='two columns settings',
                    children=[
                        html.H6("Select topics:"),
                        dcc.Loading(id="loading-mqtt-topics", color=COLORS['foreground'], children=[
                            dcc.Checklist(
                                id="mqtt-select-topics",
                                value=[],
                                labelStyle={'display': 'block'},
                                options=[{'label': topic, 'value': topic} for topic in sql_data.get_mqtt_topics()],
                                className="mqtt__topic__select",
                            ),
                        ]),
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
                ),
                html.Div(
                    className='ten columns',
                    children=[
                        dcc.Loading(id="loading-mqtt-messages", type="default", color=COLORS['foreground'], children=[
                            dash_table.DataTable(
                                id='table-mqtt-messages',
                                columns=[
                                    {"name": 'Date/Time', "id": 'datetime'},
                                    {"name": 'Topic', "id": 'topic'},
                                    {"name": 'Payload', "id": 'payload'},
                                ],
                                data=[],  # data.to_dict('records'),

                                page_action="native",
                                page_current=0,
                                page_size=25,
                                style_as_list_view=True,
                                style_header={
                                    'backgroundColor': COLORS['background-medium'],
                                    'fontWeight': 'bold'
                                },
                                style_cell={
                                    'padding': '5px',
                                    'textAlign': 'center',
                                    'backgroundColor': COLORS['background'],
                                },
                            ),
                        ]),
                    ],
                )
            ],
        ),
    ])


def layout_mqtt_live():
    if ENABLE_LIVE:
        live = html.Div(
            className='row',
            children=[
                html.Div(
                    className='two columns settings',
                    children=[
                        html.Datalist(
                            id='mqtt-topic-recent',
                            children=[html.Option(value=val) for val in sql_data.get_mqtt_topics()],
                        ),
                        dcc.Input(
                            id='mqtt-topic-input',
                            list='mqtt-topic-recent',
                            placeholder="Topic...",
                            style={
                                'backgroundColor': COLORS['background-medium'],
                                'color': COLORS['foreground'],
                                'border': f"2px solid {COLORS['foreground']}",
                                'border-radius': '4px',
                                'padding': '6px 10px',
                            },
                        ),
                        html.Button('Subscribe', id='mqtt-live-subscribe'),
                        html.Hr(),
                        html.Button(
                            'Start',
                            id='mqtt-live-start',
                            disabled=False,
                            className='start__stop__button',
                        ),
                        html.Button('Stop', id='mqtt-live-stop', disabled=True, className='start__stop__button'),
                        html.Hr(),
                        html.Div(id='mqtt-live-sub-status'),
                    ],
                ),
                html.Div(
                    className='ten columns settings',
                    children=[
                        dcc.Interval(id='mqtt-live-interval', interval=500),
                        dash_table.DataTable(
                            id='live-table',
                            columns=[
                                {"name": 'Date', "id": 'date'},
                                {"name": 'Time', "id": 'time'},
                                {"name": 'Topic', "id": 'topic'},
                                {"name": 'Quality of Service', "id": 'qos'},
                                {"name": 'Payload', "id": 'payload'},
                            ],
                            data=[],
                            editable=False,
                            fill_width=False,
                            page_action="native",
                            page_current=0,
                            page_size=20,
                            style_as_list_view=True,
                            is_focused=False,
                            style_header={
                                'backgroundColor': COLORS['background-medium'],
                                'fontWeight': 'bold'
                            },
                            style_cell={
                                'padding': '5px',
                                'textAlign': 'center',
                                'backgroundColor': COLORS['background'],
                            },
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'payload'},
                                    'textAlign': 'left'
                                }
                            ],
                            style_data={
                                'whiteSpace': 'normal',
                                'height': 'auto'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': COLORS['background-medium']
                                }
                            ],
                        ),
                    ],
                ),
            ],
        )
    else:
        live = "Live mqtt data not avaliable!"
    return live


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
        html.Div(
            id="shopping-tabs-content",
            className="app__tab__content"
        ),
    ])


def layout_shopping_overview():
    return html.Div(
        className='row',
        children=[
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className='six columns',
                        children=[
                            dcc.Loading(id="loading-shopping-montly-graph", color=COLORS['foreground'], children=[
                                dcc.Graph(
                                    id="shopping-month-graph",
                                    clear_on_unhover=True,
                                    config={
                                        'staticPlot': False,
                                        'displayModeBar': False,
                                    },
                                    className="shopping__monthly_graph graph",
                                ),
                            ], type="default"),
                        ],
                    ),
                    html.Div(
                        className='three columns',
                        children=[
                            dcc.Loading(
                                id="loading-shopping-expenses-type-graph",
                                color=COLORS['foreground'],
                                children=[
                                    dcc.Graph(
                                        id="shopping-expenses-type-graph",
                                        clear_on_unhover=True,
                                        config={
                                            'staticPlot': False,
                                            'displayModeBar': False,
                                            'displaylogo': False,
                                        },
                                        className="shopping__expenses__type_graph graph",
                                    ),
                                ],
                                type="default"
                            ),
                        ],
                    ),
                    html.Div(
                        className='three columns',
                        children=[
                            dcc.Loading(
                                id="loading-shopping-nutrition-type-graph",
                                color=COLORS['foreground'],
                                children=[
                                    dcc.Graph(
                                        id="shopping-nutrition-type-graph",
                                        clear_on_unhover=True,
                                        config={
                                            'staticPlot': False,
                                            'displayModeBar': False,
                                        },
                                        className="shopping__nutrition__type_graph graph",
                                    ),
                                ],
                                type="default"
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className='row',
                children=[
                    dcc.Loading(id="loading-shopping-overview-graph", color=COLORS['foreground'], children=[
                        dcc.Graph(
                            id="shopping-overview-graph",
                            clear_on_unhover=True,
                            config={
                                'staticPlot': False,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': [
                                    'select2d', 'lasso2d', 'autoScale2d',   # 2D
                                    'hoverClosest3d',   # 3D
                                    'hoverClosestCartesian', 'hoverCompareCartesian',   # Cartesian
                                    'zoomInGeo', 'zoomOutGeo', 'resetGeo', 'hoverClosestGeo',   # Geo
                                    'hoverClosestGl2d', 'hoverClosestPie', 'toggleHover', 'resetViews',     # other
                                    'toImage', 'toggleSpikelines', 'resetViewMapbox',   # other
                                ],
                            },
                            className="shopping__daily_graph graph",
                        ),
                    ], type="default"),
                ],
            ),
        ],
    )


def layout_shopping_add():
    return html.Div([
        dcc.Store(id='shopping-save-clear-clicks'),
        html.Br(),
        html.Div(
            className='row shopping__add__header',
            children=[
                html.Div(
                    className='one column',
                    children=[
                        html.H6("Date:", className='form__header')
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        dcc.DatePickerSingle(
                            id="shopping-new-list-date",
                            placeholder="Date...",
                            display_format='DD MM Y',
                            month_format='MM YYYY',
                            day_size=35,
                            first_day_of_week=1,
                            persistence=True,
                            persistence_type='session',
                            with_full_screen_portal=True,
                        )
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        html.H6("Sum total:", className='form__header')
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        dcc.Input(
                            id='shopping-new-price',
                            type="number",
                            placeholder='Price...',
                            # pattern=r"\d{1,3}[,.]{0,1}\d{0,2}",  # ignored in number input
                        )
                    ]
                ),
                html.Div(
                    className='one columns',
                    children=[
                        html.H6("Shop:", className='form__header')
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        html.Datalist(
                            id='shopping-shops-list',
                        ),
                        dcc.Input(
                            id='shopping-new-shop',
                            placeholder="Shop...",
                            list='shopping-shops-list',
                            # pattern=r"\d{1,3}[,.]{0,1}\d{0,2}",  # ignored in number input
                        )
                    ]
                ),
                html.Div(
                    className='one columns',
                    children=[
                        html.Button(
                            "Add another Item",
                            id='shopping-new-item-button',
                        )
                    ]
                ),
            ],
        ),
        html.Br(),
        html.Datalist(
            id='shopping-items-list',
        ),
        html.Div(
            id='shopping-add-items-list',
            className='shopping__add__items',
            children=[
                html.Div(
                    className='row add__items',
                    children=[
                        html.Div(
                            className='offset-by-two two columns',
                            children=[
                                dcc.Input(
                                    id={
                                        'type': 'shopping-new-item',
                                        'id': n,
                                    },
                                    placeholder="Item...",
                                    list='shopping-items-list',
                                )
                            ]
                        ),
                        html.Div(
                            className='two columns',
                            children=[
                                dcc.Input(
                                    id={
                                        'type': 'shopping-new-item-price',
                                        'id': n,
                                    },
                                    placeholder="Item Price...",
                                    type='number',
                                )
                            ]
                        ),
                        html.Div(
                            className='two columns',
                            children=[
                                dcc.Input(
                                    id={
                                        'type': 'shopping-new-item-note',
                                        'id': n,
                                    },
                                    placeholder="Note...",
                                )
                            ]
                        ),
                        html.Div(
                            className='offset-by-one column one column',
                            children=[
                                html.Button(
                                    "Remove Item",
                                    id={
                                        'type': 'shopping-remove-item',
                                        'id': n,
                                    },
                                )
                            ]
                        ),
                    ],
                )
                for n in range(0, N_SHOPPING_ITEMS)
            ]
        ),
        html.Br(),
        html.Div(
            className='row shopping__add__submit',
            children=[
                html.Div(
                    className='offset-by-one-third column two columns',
                    children=[
                        html.Button(
                            'Submit',
                            id='shopping-submit-list',
                        )
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        html.Button(
                            'Clear',
                            id='shopping-clear-list',
                        )
                    ]
                ),
                html.Div(
                    className='three columns',
                    children=[
                        dbc.Alert(
                            id='shopping-status-alert',
                            duration=10000,
                            fade=True,
                        ),
                    ]
                ),
            ]
        ),
    ], className='shopping__add__container')


def get_states(sub_color, active_color, load_color):
    return [
        html.Div(
            className='row',
            children=[
                html.Div(
                    className="one-third column",
                    children=[
                        daq.Indicator(
                            label="Service Running",
                            color=sub_color,
                            className="general__services__state",
                        ),
                    ]
                ),
                html.Div(
                    className="one-third column",
                    children=[
                        daq.Indicator(
                            label="Service State",
                            color=active_color,
                            className="general__services__state",
                        ),
                    ]
                ),
                html.Div(
                    className="one-third column",
                    children=[
                        daq.Indicator(
                            label="State Config File",
                            color=load_color,
                            className="general__services__state",
                        ),
                    ]
                ),
            ]
        )
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
        layout = dcc.Loading(id="loading-2", color=COLORS['foreground'], children=[
            layout_shopping_overview()
        ], type="default")
    elif tab == 'shopping-add-tab':
        layout = layout_shopping_add()
    return layout


"""@APP.callback(Output('current-data-headers', 'children'),
              [Input('data-overview-update', 'n_intervals'),
               Input('data-overview-values', 'value')])
def update_current_data_headers(interval, overview_values):
    return [
        html.Div(
            children=[
                html.H6(f"Current {value.capitalize()}", className="temp__current__title title__center"),
            ],
            className=DIV_COLUMNS[len(overview_values)],
        ) for value in overview_values
    ]
"""

@APP.callback(Output('current-data', 'children'),
              [Input('data-overview-update', 'n_intervals'),
               Input('data-overview-values', 'value')])
def update_current_data(interval, overview_values):
    gauges = []
    for value in overview_values:
        min_val, max_val, last = sql_data.get_gauge_data(value)
        min_val = round(min_val)
        max_val = ceil(max_val)
        step = round((max_val - min_val) / 3)

        if value in UNITS.keys():
            unit = UNITS[value]
        else:
            unit = ''

        gauges.append(
            html.Div(
                children=[
                    daq.Gauge(
                        id="current-temp-gauge",
                        label=value.capitalize(),
                        size=150,
                        value=last,
                        min=min_val,
                        max=max_val,
                        showCurrentValue=True,
                        units=unit,
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
                className=DIV_COLUMNS[len(overview_values)],
            )
        )
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
                'color': COLORS['foreground-dark']
            },
            'margin': {'l': 30, 'b': 30, 'r': 10, 't': 10},
            # 'width': '100%',
            'height': '400',
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
                    'color': COLORS['foreground-dark']
                },
                'margin': {'l': 30, 'b': 30, 'r': 10, 't': 10},
                # 'width': '100%',
                'height': '500',
            }
        }
    else:
        return EMPTY_GRAPH


@APP.callback(Output('table-mqtt-messages', 'data'),
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
                'backgroundColor': COLORS['background-medium'],
                'color': COLORS['foreground'],
                'border': f"2px solid {COLORS['green']}",
                'border-radius': '4px',
                'padding': '6px 10px',
            }
        else:
            style = {
                'backgroundColor': COLORS['background-medium'],
                'color': COLORS['foreground'],
                'border': f"2px solid {COLORS['red']}",
                'border-radius': '4px',
                'padding': '6px 10px',
            }
    else:
        style = {
            'backgroundColor': COLORS['background-medium'],
            'color': COLORS['foreground'],
            'border': f"2px solid {COLORS['foreground']}",
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
              [Input('general-stats-update', 'n_intervals')])
def update_dashboard_service(interval):
    data = pi_data.get_service_data("dashboard")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('datalogger-states', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def update_mqtt_handler_service(interval):
    data = pi_data.get_service_data("mqtthandler")
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('mqtt-states', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def update_probemon_service(interval):
    data = pi_data.get_service_data("probemon", user=False)
    colors = get_state_colors(data)
    return get_states(*colors)


@APP.callback(Output('cpu-stats', 'children'),
              [Input('general-stats-update', 'n_intervals')])
def cpu_state(interval):
    cpu_percent = pi_data.get_cpu_percent()
    return daq.GraduatedBar(
        max=100,
        value=cpu_percent,
        showCurrentValue=True,
        className='graduated__bar',
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


@APP.callback(
    Output('shopping-month-graph', 'figure'),
    [Input("loading-shopping-overview-graph", 'loading_state')]
)
def get_shopping_monthly_overview(state):
    six_months_ago = datetime.now()-relativedelta(months=6)
    six_months_ago = datetime(six_months_ago.year, six_months_ago.month, 1)

    data = sql_data.get_shopping_expenses_by_date(six_months_ago)
    curr_month = data.Date.dt.month.unique()[-1]
    unique_months = data.Date.dt.month.unique()

    max_min = list(
        zip(
            *[
                (x.Payment.cumsum().max(), x.Payment.cumsum().min())
                for _, x in data[data.Date.dt.month != curr_month].set_index('Date').groupby(lambda x: x.month)
            ]
        )
    )

    y1_max, y1_min = max(max_min[0]), min(max_min[1])
    y2_min, y2_max = (
        data[data.Date.dt.month == curr_month].Payment.min(),
        data[data.Date.dt.month == curr_month].Payment.max(),
    )
    y1_range_min, y1_range_max, y1_dtick, y2_range_min, y2_range_max, y2_dtick = graph_helper.calculate_ticks(
        y1_min, y1_max, y2_min, y2_max
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for month in unique_months:
        months_data = pd.DataFrame({
            'Days': data[data.Date.dt.month == month].Date.dt.day,
            'Payment': data[data.Date.dt.month == month].Payment.cumsum()
        })
        months_data.loc[-1] = 0
        months_data.index = months_data.index + 1
        months_data = months_data.sort_index()
        if months_data.Days.iloc[-1] != 31 and (month != unique_months[-1] or month != datetime.now().month):
            months_data = months_data.append(
                {'Days': 31, 'Payment': np.interp([31], months_data.Days, months_data.Payment)[0]},
                ignore_index=True
            )

        trace = go.Scatter(
            mode='lines',
            hovertemplate='%{y:.2f}€',
            x=months_data.Days,
            y=months_data.Payment,
            name=month_name[month],
            yaxis='y2',
        )

        if month == unique_months[-1]:
            trace.line = {'color': COLORS['foreground']}

        fig.add_trace(
            trace,
            secondary_y=True,
        )
        if month == unique_months[-1]:
            fig.add_trace(
                go.Bar(
                    opacity=0.5,
                    hovertemplate='%{y:.2f}€',
                    x=data[data.Date.dt.month == month].Date.dt.day,
                    y=data[data.Date.dt.month == month].Payment,
                    name=month_name[month],
                    marker={
                        'color': COLORS['foreground'],
                    },
                ),
                secondary_y=False,
            )

    fig.update_layout({
        'autosize': True,
        'barmode': 'overlay',
        'coloraxis': {
            'colorbar': {
                'outlinewidth': 0,
                'bordercolor': COLORS['background'],
                'bgcolor': COLORS['background'],
            },
        },
        'colorway': COLORS['colorway'],
        'dragmode': False,
        'font': {
            'color': COLORS['foreground'],
        },
        'legend': {
            'orientation': 'h',
        },
        'margin': {
            'l': 10, 'r': 10, 't': 10, 'b': 10, 'pad': 0,
        },
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background'],
        'xaxis': {
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
        'yaxis': {
            'side': 'right',
            'range': [y2_range_min, y2_range_max],
            'dtick': y2_dtick,
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
        'yaxis2': {
            'side': 'left',
            'range': [y1_range_min, y1_range_max],
            'dtick': y1_dtick,
            'overlaying': 'y',
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
    })
    return fig


@APP.callback(
    Output('shopping-expenses-type-graph', 'figure'),
    [Input('loading-shopping-expenses-type-graph', 'loading_state')]
)
def get_shopping_expenses_type_overview(state):
    # this_month = datetime(datetime.now().year, datetime.now().month, 1)
    # expenses_this_month = sql_data.get_shopping_expenses_by_date(this_month)
    fig = go.Figure()

    fig.update_layout({
        'autosize': True,
        'barmode': 'overlay',
        'coloraxis': {
            'colorbar': {
                'outlinewidth': 0,
                'bordercolor': COLORS['background'],
                'bgcolor': COLORS['background'],
            },
        },
        'colorway': COLORS['colorway'],
        'dragmode': False,
        'font': {
            'color': COLORS['foreground'],
        },
        'legend': {
            'orientation': 'h',
        },
        'margin': {
            'l': 10, 'r': 10, 't': 10, 'b': 10, 'pad': 0,
        },
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background'],
        'xaxis': {
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
        'yaxis': {
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
    })
    return fig


@APP.callback(
    Output('shopping-nutrition-type-graph', 'figure'),
    [Input('loading-shopping-nutrition-type-graph', 'loading_state')]
)
def get_shopping_nutrition_type_graph(state):
    fig = go.Figure()

    fig.update_layout({
        'autosize': True,
        'barmode': 'overlay',
        'coloraxis': {
            'colorbar': {
                'outlinewidth': 0,
                'bordercolor': COLORS['background'],
                'bgcolor': COLORS['background'],
            },
        },
        'colorway': COLORS['colorway'],
        'dragmode': False,
        'font': {
            'color': COLORS['foreground'],
        },
        'legend': {
            'orientation': 'h',
        },
        'margin': {
            'l': 10, 'r': 10, 't': 10, 'b': 10, 'pad': 0,
        },
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background'],
        'xaxis': {
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
        'yaxis': {
            'fixedrange': True, 'rangemode': 'tozero',
            'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
            'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
            'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
        },
    })
    return fig


@APP.callback(
    Output('shopping-overview-graph', 'figure'),
    [Input("loading-shopping-overview-graph", 'loading_state')]
)
def get_shopping_total_overview(state):
    df_days = sql_data.get_unique_shopping_days()
    shops = sql_data.get_unique_shopping_shops()
    shops = shops.sort_values('Shop')

    data = []
    for shop in shops.Shop:
        expense = sql_data.get_shopping_expenses_per_shop(shop)
        df_days = df_days.join(expense)
        bar = go.Bar(
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
        )

        if shop.lower() == 'rewe':
            bar.marker['color'] = COLORS['colorway'][0]
        elif shop.lower() == 'aldi':
            bar.marker['color'] = COLORS['colorway'][1]
        elif shop.lower() == 'amazon':
            bar.marker['color'] = COLORS['colorway'][2]
        elif shop.lower() == 'bike24':
            bar.marker['color'] = COLORS['foreground']

        data.append(bar)

    fig = go.Figure(
        data=data,
        layout={
            'autosize': True,
            'barmode': 'stack',
            'coloraxis': {
                'colorbar': {
                    'outlinewidth': 0,
                    'bordercolor': COLORS['background'],
                    'bgcolor': COLORS['background'],
                },
            },
            'colorway': COLORS['colorway'][3:],
            'font': {
                'color': COLORS['foreground'],
            },
            'legend': {
                'orientation': 'h',
            },
            'margin': {
                'l': 10, 'r': 10, 't': 10, 'b': 10, 'pad': 0,
            },
            'paper_bgcolor': COLORS['background'],
            'plot_bgcolor': COLORS['background'],
            'xaxis': {
                'type': 'date',
                'range': [datetime(datetime.now().year-1, datetime.now().month, datetime.now().day), datetime.now()],
                'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
                'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
                'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
            },
            'yaxis': {
                'showline': True, 'linewidth': 1, 'linecolor': COLORS['border-medium'],
                'showgrid': True, 'gridwidth': 1, 'gridcolor': COLORS['border-medium'],
                'zeroline': True, 'zerolinewidth': 1, 'zerolinecolor': COLORS['border-medium'],
            },
        }
    )
    return fig


@APP.callback(
    Output('shopping-shops-store', 'data'),
    [Input('shopping-shops-store', 'modified_timestamp')],
    [State('shopping-shops-store', 'data')],
)
def init_shops_store(last_modified, data):
    return [html.Option(value=val) for val in sql_data.get_unique_shopping_shops().Shop]


@APP.callback(
    Output('shopping-shops-list', 'children'),
    [Input('shopping-shops-store', 'data')]
)
def get_shopping_shops(data):
    logger.debug(f"Shops from store requested.")
    return data


@APP.callback(
    Output('shopping-products-store', 'data'),
    [Input('shopping-products-store', 'modified_timestamp')],
    [State('shopping-products-store', 'data')],
)
def init_products_store(last_modified, data):
    return [html.Option(value=val) for val in sql_data.get_unique_shopping_items().Product]


@APP.callback(
    Output(f'shopping-items-list', 'children'),
    [Input('shopping-products-store', 'data')],
)
def get_shopping_products(data):
    return data


@APP.callback(
    Output('shopping-add-items-list', 'children'),
    [Input('shopping-new-item-button', 'n_clicks'),
     Input({'type': 'shopping-remove-item', 'id': ALL}, 'n_clicks')],
    [State('shopping-add-items-list', 'children')]
)
def shopping_manage_items(n_clicks, indexes, old_shopping_add_list):
    logger.info(f"Update Shopping items list called.")
    logger.info(f"      Indexes: {indexes}.")

    if any(indexes):
        # Remove item from list
        list_items_to_remove = [idx for idx, value in enumerate(indexes) if value]
        for index in list_items_to_remove:
            old_shopping_add_list.pop(index)
        return old_shopping_add_list

    if n_clicks is None:
        raise PreventUpdate

    # Add a new list item
    return old_shopping_add_list + [
        html.Div(
            className='row add__items',
            children=[
                html.Div(
                    className='offset-by-two two columns',
                    children=[
                        dcc.Input(
                            id={
                                'type': 'shopping-new-item',
                                'id': n_clicks+N_SHOPPING_ITEMS-1,
                            },
                            placeholder="Item...",
                            list='shopping-items-list',
                        )
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        dcc.Input(
                            id={
                                'type': 'shopping-new-item-price',
                                'id': n_clicks+N_SHOPPING_ITEMS-1,
                            },
                            placeholder="Item Price...",
                            type='number',
                        )
                    ]
                ),
                html.Div(
                    className='two columns',
                    children=[
                        dcc.Input(
                            id={
                                'type': 'shopping-new-item-note',
                                'id': n_clicks+N_SHOPPING_ITEMS-1,
                            },
                            placeholder="Note...",
                        )
                    ]
                ),
                html.Div(
                    className='offset-by-one column one column',
                    children=[
                        html.Button(
                            "Remove Item",
                            id={
                                'type': 'shopping-remove-item',
                                'id': n_clicks+N_SHOPPING_ITEMS-1,
                            },
                        )
                    ]
                ),
            ],
        ),
    ]


@APP.callback(
    [Output('shopping-status-alert', 'children'),
     Output('shopping-status-alert', 'className'),
     Output('shopping-status-alert', 'is_open')],
    [Input('shopping-submit-list', 'n_clicks')],
    [State('shopping-new-list-date', 'date'),
     State('shopping-new-price', 'value'),
     State('shopping-new-shop', 'value'),
     State({'type': 'shopping-new-item', 'id': ALL}, 'value'),
     State({'type': 'shopping-new-item-price', 'id': ALL}, 'value'),
     State({'type': 'shopping-new-item-note', 'id': ALL}, 'value')]
)
def save_shopping_list(submit_clicks, date, price, shop, items, prices, notes):
    logger.debug(f"Save shopping list called. button clicks: {submit_clicks}.")
    logger.debug(f"Items: {date, price, shop, items, prices, notes}.")
    if submit_clicks is None:
        return "", "", False

    shopping_list_prelim = pd.DataFrame(data={
        'Date': datetime.strptime(date, '%Y-%m-%d') if date else None,
        'Payment': float(price) if price else None,
        'Shop': shop,
        'Product': items,
        'Price': prices,
        'Note': notes,
    })
    logger.debug(f"prelim: {shopping_list_prelim}.")
    shopping_list = shopping_list_prelim.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    shopping_list = shopping_list_prelim.dropna(subset=['Product', 'Price'], how='all')
    logger.debug(f"after drop: {shopping_list}.")
    if shopping_list.empty:
        return "Pelase add at least one product to the list.", "shopping_status_alert_warning", True

    bad_entry_list = []
    if shopping_list.Date.isna().any():
        bad_entry_list.append(html.Li("Date is missing."))
    if shopping_list.Payment.isna().any():
        bad_entry_list.append(html.Li("Sum total is missing."))
    if shopping_list.Shop.isna().any():
        bad_entry_list.append(html.Li("Shop is missing."))
    if shopping_list.Product.isna().any():
        missing_products = shopping_list.Product.isna()
        bad_prices = [str(pproduct) for pproduct in shopping_list.Price[missing_products].tolist()]
        bad_entry_list.append(html.Li("These Products' price is missing: " + ", ".join(bad_prices)))
    if shopping_list.Price.isna().any():
        missing_prices = shopping_list.Price.isna()
        bad_products = [str(pprice) for pprice in shopping_list.Product[missing_prices].tolist()]
        bad_entry_list.append(html.Li("These Products' price is missing: " + ", ".join(bad_products)))

    if bad_entry_list:
        children = [html.H6("Can't add shopping list:"), html.Ul(bad_entry_list)]
        return children, "shopping_status_alert_fail", True
    else:
        logger.debug(f"Pandas Dataframe Shopping List: {shopping_list}")
        sql_data.add_shopping_list(shopping_list)
        return "Successfully added shopping list", "shopping_status_alert_success", True


@APP.callback(
    [Output('shopping-new-price', 'value'),
     Output('shopping-new-shop', 'value'),
     Output({'type': 'shopping-new-item', 'id': ALL}, 'value'),
     Output({'type': 'shopping-new-item-price', 'id': ALL}, 'value'),
     Output({'type': 'shopping-new-item-note', 'id': ALL}, 'value')],
    [Input('shopping-clear-list', 'n_clicks')],
    [State({'type': 'shopping-new-item', 'id': ALL}, 'value'),
     State('shopping-save-clear-clicks', 'data')]
)
def clear_shopping_list(n_clicks, items, old_clicks):
    logger.info(f"Clear Shopping item values called. clicks: new: {n_clicks} old: {old_clicks}.")
    if n_clicks is None or n_clicks <= old_clicks['clicks']:
        raise PreventUpdate
    empty = ['' for _ in items]
    return '', '', empty, empty, empty


@APP.callback(
    Output('shopping-save-clear-clicks', 'data'),
    [Input('shopping-clear-list', 'n_clicks')],
)
def init_shopping_clear_clicks_store(n_clicks):
    logger.debug(f"Clicks store: click {n_clicks}")
    if n_clicks is None:
        return {'clicks': 0}
    else:
        return {'clicks': n_clicks}


if __name__ == "__main__":
    APP.run_server(debug=True, port=5002, host='0.0.0.0', threaded=True)
