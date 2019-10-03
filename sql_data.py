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


def csv_to_db(filepath):
    DATABASE = 'data.db'
    DATETIME = 'datetime'
    TEMPERATURE = 'temperature'

    res_df = pandas.read_csv(filepath, encoding="UTF-16")
    #res_df = pandas.read_csv("~/Schreibtisch/week-38-results.csv", encoding="UTF-8")
    #print(res_df)
    #res_df.insert(0, DATETIME, pandas.to_datetime(res_df['date'] + " " + res_df['time']))
    res_df.insert(0, DATETIME, res_df.apply(lambda x: datetime.strptime(x['date'] + " " + x['time'], '%d-%m-%Y %H:%M:%S'), axis=1))
    res_df = res_df.drop(columns=['date', 'time'])
    print(res_df)

    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
        res_df[[DATETIME, TEMPERATURE]].to_sql(TEMPERATURE, con=conn, index=False, index_label=DATETIME, if_exists='append')


def add_temp_to_db(date_time, temperature):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'temperature'
                            ('datetime', 'temperature') 
                            VALUES (?, ?);"""
            data_tuple = (date_time, temperature)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            sqlConnection.commit()
            print("Message added successfully.")


def add_humidity_to_db(date_time, humidity):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'humidity'
                            ('datetime', 'humidity') 
                            VALUES (?, ?);"""
            data_tuple = (date_time, humidity)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            sqlConnection.commit()
            print("Message added successfully.")


def add_humidity_to_db(date_time, brightness):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'brightness'
                            ('datetime', 'brightness') 
                            VALUES (?, ?);"""
            data_tuple = (date_time, brightness)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            sqlConnection.commit()
            print("Message added successfully.")


def add_pressure_to_db(date_time, pressure):
        with sqlite3.connect(DATABASE) as connection:

            # insert developer detail
            insert_with_param = """INSERT INTO 'pressure'
                            ('datetime', 'pressure') 
                            VALUES (?, ?);"""
            data_tuple = (date_time, pressure)

            cursor = connection.cursor()
            cursor.execute(insert_with_param, data_tuple)
            sqlConnection.commit()
            print("Message added successfully.")



if __name__ == "__main__":
    get_min_temp()
    get_max_temp()
    get_last_temp()
    get_min_datetime()
    last_date=get_max_datetime()
    get_day_temp(last_date)
    get_day_temp_pandas()
    quit()
