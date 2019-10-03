import sqlite3
import pandas
from datetime import datetime, timedelta

DATABASE = 'data.db'
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
        print("Query database for max value of column 'temperature' from table 'temperature'.")
        max_temp = cursor.execute("SELECT MAX(temperature) FROM temperature").fetchone()[0]
    if max_temp < MAX_TEMP:
        print(f"Found max temperature: {max_temp}.")
    else:
        print("Max temp could not be found.")
    return max_temp

def get_min_temp():
    min_temp = MIN_TEMP
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        print("Query database for min value of column 'temperature' from table 'temperature'.")
        min_temp = cursor.execute("SELECT MIN(temperature) FROM temperature").fetchone()[0]
    if min_temp > MIN_TEMP:
        print(f"Found min temperature: {min_temp}.")
    else:
        print("Max temp could not be found.")
    return min_temp

def get_last_temp():
    last = LAST_TEMP
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        print("Query database for newest value of column 'temperature' from table 'temperature', ordered by column 'datetime'.")
        last = cursor.execute("SELECT temperature FROM temperature ORDER BY datetime DESC LIMIT 1").fetchone()[0]
    if last > LAST_TEMP:
        print(f"Found last temperature: {last}.")
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
        print("Query database for max value of column 'datetime' from table 'temperature'.")
        max_datetime = cursor.execute("SELECT datetime FROM temperature ORDER BY datetime DESC LIMIT 1").fetchone()[0]

    if max_datetime < MAX_DATETIME:
        print(f"Found max datetime: {max_datetime}.")
    else:
        print("Max datetime could not be found.")
    return max_datetime

def get_min_datetime():
    min_datetime = MIN_DATETIME
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()
        print("Query database for min value of column 'datetime' from table 'temperature'.")
        min_datetime = pandas.Timestamp(cursor.execute("SELECT MIN(datetime) FROM temperature").fetchone()[0])

    if min_datetime > MIN_DATETIME:
        print(f"Found min datetime: {min_datetime}.")
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
        print(f"Query database for temperature-data of the last 24 hours.")
        data = cursor.execute("SELECT * FROM temperature WHERE datetime > ?", 
                              (query_datetime, )).fetchall()

    if data:
        print(f"Successfully recieved {len(data)} Values.")
    else:
        print("Could not get any values.")
    return data

def get_day_temp_pandas():
    data = None
    
    with sqlite3.connect(
        DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:

        cursor = connection.cursor()
        print("Query database for max value of column 'datetime' from table 'temperature'.")
        max_datetime = cursor.execute("SELECT datetime FROM temperature ORDER BY datetime DESC LIMIT 1").fetchone()[0]
        query_datetime = max_datetime - timedelta(hours=24)

        print(f"Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pandas.read_sql("SELECT * FROM temperature WHERE datetime > ?", params=(query_datetime, ), parse_dates=['datetime'], con=connection)

    return data

if __name__ == "__main__":
    get_min_temp()
    get_max_temp()
    get_last_temp()
    get_min_datetime()
    last_date=get_max_datetime()
    get_day_temp(last_date)
    print(get_day_temp_pandas())
    quit()
