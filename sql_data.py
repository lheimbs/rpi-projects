#!/usr/bin/env python3
# coding=utf-8

import sqlite3
from datetime import datetime, timedelta
import pandas

DATABASE = 'data.db'
TABLE = 'room-data'
DATETIME = 'datetime'
TEMPERATURE = 'temperature'
MAX_TEMP = 50
MIN_TEMP = -20
LAST_TEMP = 0
MAX_DATETIME = pandas.Timestamp.now()
MIN_DATETIME = pandas.Timestamp("2019-07-01-T00")


def get_max_temp():
    max_temp = MAX_TEMP
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        #print("Query database for max value of column 'temperature' from table 'room'.")
        max_temp = cursor.execute("SELECT MAX(temperature) FROM 'room-data'").fetchone()[0]
    if max_temp < MAX_TEMP:
        print("Found max temperature: {}.".format(max_temp))
    else:
        print("Max temp could not be found.")
    return max_temp


def get_min_temp():
    min_temp = MIN_TEMP
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        #print("Query database for min value of column 'temperature' from table 'room'.")
        min_temp = cursor.execute("SELECT MIN(temperature) FROM 'room-data'").fetchone()[0]
    if min_temp > MIN_TEMP:
        print("Found min temperature: {}.".format(min_temp))
    else:
        print("Max temp could not be found.")
    return min_temp

def get_last_temp():
    last = LAST_TEMP
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        #print("Query database for newest value of column 'temperature' from table 'room', ordered by column 'datetime'.")
        last = cursor.execute("SELECT temperature FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]
    if last > LAST_TEMP:
        print("Found last temperature: {}.".format(last))
    else:
        print("Max temp could not be found.")
    return last

def get_max_datetime():
    max_datetime = MAX_DATETIME
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as connection:
        cursor = connection.cursor()
        #print("Query database for max value of column 'datetime' from table 'room'.")
        max_datetime = cursor.execute("SELECT datetime FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]

    if max_datetime < MAX_DATETIME:
        print("Found max datetime: {}.".format(max_datetime))
    else:
        print("Max datetime could not be found.")
    return max_datetime

def get_min_datetime():
    min_datetime = MIN_DATETIME
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()
        #print("Query database for min value of column 'datetime' from table 'room'.")
        min_datetime = pandas.Timestamp(cursor.execute("SELECT MIN(datetime) FROM 'room-data'").fetchone()[0])

    if min_datetime > MIN_DATETIME:
        print("Found min datetime: {}.".format(min_datetime))
    else:
        print("Max datetime could not be found.")
    return min_datetime

def get_day_temp(start_datetime):
    data = []
    query_datetime = start_datetime - timedelta(hours=24)
    with sqlite3.connect(DATABASE,
                         detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                        ) as connection:
        cursor = connection.cursor()
        #print("Query database for temperature-data of the last 24 hours.")
        data = cursor.execute("SELECT datetime, temperature FROM 'room-data' WHERE datetime > ?", 
                              (query_datetime, )).fetchall()

    if data:
        print("Successfully recieved {} Values.".format(len(data)))
    else:
        print("Could not get any values.")
    return data

def get_day_temp_pandas():
    data = None
    
    with sqlite3.connect(
        DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:

        cursor = connection.cursor()
        #print("Query database for max value of column 'datetime' from table 'room'.")
        max_datetime = cursor.execute("SELECT datetime FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]
        query_datetime = max_datetime - timedelta(hours=24)

        #print("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql("SELECT datetime, temperature FROM 'room-data' WHERE datetime > ?", params=(query_datetime, ), parse_dates=['datetime'], con=connection)
        print("Successfully queried temperature data from the last 24hrs")

    return data

def get_temp_history(start_time, end_time):
    data = None

    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        #print("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql(
            "SELECT datetime, temperature FROM 'room-data' WHERE datetime BETWEEN ? and ?;", 
            params=(start_time, end_time), 
            parse_dates=['datetime'], 
            con=connection
        )
        print("Successfully queried temperature data between {} and {}".format(
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


def add_to_db(date_time, temperature, humidity, brightness, pressure):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'room-data'
                            ('datetime', 'temperature', 'humidity', 'brightness', 'pressure') 
                            VALUES (?, ?, ?, ?, ?);"""
            data_tuple = (date_time, temperature, humidity, brightness, pressure)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            connection.commit()
            print("Data added successfully.")

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
        print("MQTT-Message added successfully.")

def get_mqtt_messages():
    data = None
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        #print("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql(
            "SELECT * FROM 'mqtt_messages' ORDER BY datetime ASC;",
            parse_dates=['datetime'],
            con=connection
        )
        print("Successfully queried mqtt messages.")
    return data


if __name__ == "__main__":
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
