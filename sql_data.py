#!/usr/bin/env python3
# coding=utf-8

import sqlite3
import pandas
import logging
from datetime import datetime, timedelta

DATABASE = 'data.db'
TABLE = 'room-data'
DATETIME = 'datetime'
TEMPERATURE = 'temperature'
MAX_VAL = 9999
MIN_VAL = -9999
LAST_VAL = 0
MAX_DATETIME = pandas.Timestamp.now()
MIN_DATETIME = pandas.Timestamp("2019-07-01-T00")
VALUE_TYPES = ['temperature', 'humidity', 'pressure', 'altitude', 'brightness']

logger = logging.getLogger(__name__)

def get_max_value(value_type):
    if value_type not in VALUE_TYPES:
        raise ValueError(f"Invalid value '{value_type}'. Expected one of: {VALUE_TYPES}")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        logger.info(f"Query database for max value of column {value_type} from table 'room-data'.")
        max_val = cursor.execute(f"SELECT MAX({value_type}) FROM 'room-data'").fetchone()[0]
    if max_val == 'nan':
        return MAX_VAL
    else:
        max_val = float(max_val)

    if max_val < MAX_VAL:
        logger.info(f"Found max {value_type}: {max_val}")
    else:
        logger.warning(f"Maximum in {value_type} could not be found.")
    return max_val


def get_min_value(value_type):
    if value_type not in VALUE_TYPES:
        raise ValueError(f"Invalid value '{value_type}'. Expected one of: {VALUE_TYPES}")
    min_val = MIN_VAL
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        logger.info(f"Query database for min value of column {value_type} from table 'room-data'.")
        min_val = cursor.execute(f"SELECT MIN({value_type}) FROM 'room-data'").fetchone()[0]
    if min_val == 'nan':
        return MIN_VAL
    else:
        min_val = float(min_val)

    if min_val < MIN_VAL:
        logger.info(f"Found min {value_type}: {min_val}")
    else:
        logger.warning(f"Minimum in {value_type} could not be found.")
    return min_val


def get_last_value(value_type):
    if value_type not in VALUE_TYPES:
        raise ValueError(f"Invalid value '{value_type}'. Expected one of: {VALUE_TYPES}")
    last_val = LAST_VAL
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        logger.info(f"Query database for newest value of column '{value_type}' from table 'room-data', ordered by column 'datetime'.")
        last_val = cursor.execute(f"SELECT {value_type} FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]
    if last_val > LAST_VAL:
        logger.info(f"Found last value from {value_type}: {last_val}")
    else:
        logger.warning("Max temp could not be found.")
    return last_val

def get_max_datetime():
    max_datetime = MAX_DATETIME
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as connection:
        cursor = connection.cursor()
        logger.info("Query database for max value of column 'datetime' from table 'room-data'.")
        max_datetime = cursor.execute("SELECT datetime FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]

    if max_datetime < MAX_DATETIME:
        logger.info("Found max datetime: {}.".format(max_datetime))
    else:
        logger.warning("Max datetime could not be found.")
    return max_datetime

def get_min_datetime():
    min_datetime = MIN_DATETIME
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()
        logger.info("Query database for min value of column 'datetime' from table 'room-data'.")
        min_datetime = pandas.Timestamp(cursor.execute("SELECT MIN(datetime) FROM 'room-data'").fetchone()[0])

    if min_datetime > MIN_DATETIME:
        logger.info("Found min datetime: {}.".format(min_datetime))
    else:
        logger.warning("Max datetime could not be found.")
    return min_datetime


def get_day_temp():
    data = None
    max_datetime = get_max_datetime()
    query_datetime = max_datetime - timedelta(hours=24)
    
    with sqlite3.connect(
        DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        cursor = connection.cursor()
        logger.info("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql("SELECT datetime, temperature FROM 'room-data' WHERE datetime > ?", params=(query_datetime, ), parse_dates=['datetime'], con=connection)
        logger.info("Successfully queried temperature data from the last 24hrs")
    return data


def get_day_data(values):
    for value in values:
        if value not in VALUE_TYPES:
            raise ValueError(f"Invalid value '{value}'. Expected one of: {VALUE_TYPES}")
    data = None
    max_datetime = get_max_datetime()
    query_datetime = max_datetime - timedelta(hours=24)
    
    with sqlite3.connect(
        DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        cursor = connection.cursor()
        logger.info(f"Query database for {', '.join(values)} of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql(f"SELECT datetime, {', '.join(values)} FROM 'room-data' WHERE datetime > ?", params=(query_datetime, ), parse_dates=['datetime'], con=connection)
        logger.info("Successfully queried temperature data from the last 24hrs")
    return data


def get_temp_history(start_time, end_time):
    data = None

    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        logger.info("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql(
            "SELECT datetime, temperature FROM 'room-data' WHERE datetime BETWEEN ? and ?;", 
            params=(start_time, end_time), 
            parse_dates=['datetime'], 
            con=connection
        )
        logger.info("Successfully queried temperature data between {} and {}".format(
            datetime.strftime(start_time, '%d-%m-%Y'),
            datetime.strftime(end_time, '%d-%m-%Y'),
        ))
    return data


def csv_to_db(filepath):
    db = 'data.db'
    dt = 'datetime'

    try:
        res_df = pandas.read_csv(filepath, encoding="UTF-16")
    except:
        res_df = pandas.read_csv(filepath, encoding="UTF-8")
    #print(res_df)
    #res_df.insert(0, dt, pandas.to_datetime(res_df['date'] + " " + res_df['time']))
    res_df.insert(0, dt, res_df.apply(lambda x: datetime.strptime(x['date'] + " " + x['time'], '%d-%m-%Y %H:%M:%S'), axis=1))
    try:
        res_df = res_df.drop(columns=['date', 'time'])
    except:
        res_df = res_df.drop(['date', 'time'], axis=1)
    res_df['pressure'] = 0
    print(res_df)

    with sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
        res_df.to_sql('room', con=conn, index=False, index_label=dt, if_exists='append')


def add_room_data_to_db(date_time, temperature, humidity, brightness, pressure):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'room-data'
                            ('datetime', 'temperature', 'humidity', 'brightness', 'pressure') 
                            VALUES (?, ?, ?, ?, ?);"""
            data_tuple = (date_time, temperature, humidity, brightness, pressure)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            connection.commit()
            logger.info("Data added successfully.")

def add_mqtt_to_db(date_time, topic, message):
    with sqlite3.connect(DATABASE) as connection:
        # insert developer detail
        insert_with_param = """INSERT INTO 'mqtt_messages'
                        ('datetime', 'topic', 'payload') 
                        VALUES (?, ?, ?);"""

        data_tuple = (date_time, topic, message)

        cursor = connection.cursor()
        cursor.execute(insert_with_param, data_tuple)
        connection.commit()
        logger.info("MQTT-Message '%s' added successfully.", message)

def get_mqtt_messages():
    data = None
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        logger.info("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql(
            "SELECT * FROM 'mqtt_messages' ORDER BY datetime DESC;",
            parse_dates=['datetime'],
            con=connection
        )
        logger.info("Successfully queried mqtt messages.")
    return data


def log_to_db():
    import os
    f='/home/pi/log/'
    file=os.listdir(f)
    file.remove('mqtt.log')
    file.remove('data_logger.log')
    file.sort()
    file.append(file.pop(0))
    print(file)
    input()

    for ff in file:
        csv_to_db(f+ff)
        input()
    quit()

    get_min_temp()
    get_max_temp()
    get_last_temp()
    get_min_datetime()
    last_date=get_max_datetime()
    get_day_temp(last_date)
    get_day_temp_pandas()
    quit()

