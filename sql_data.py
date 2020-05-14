#!/usr/bin/env python3
# coding=utf-8

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta

DATABASE = 'data.db'
TABLE = 'room-data'
DATETIME = 'datetime'
TEMPERATURE = 'temperature'
MAX_VAL = 9999
MIN_VAL = -9999
LAST_VAL = 0
MAX_DATETIME = pd.Timestamp.now()
MIN_DATETIME = pd.Timestamp("2019-07-01-T00")
VALUE_TYPES = ['temperature', 'humidity', 'pressure', 'altitude', 'brightness']

logger = logging.getLogger('dashboard.sql_data')


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

    logger.info(f"Found max {value_type}: {max_val}")
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

    logger.info(f"Found min {value_type}: {min_val}")
    return min_val


def get_last_value(value_type):
    if value_type not in VALUE_TYPES:
        raise ValueError(f"Invalid value '{value_type}'. Expected one of: {VALUE_TYPES}")
    last_val = LAST_VAL
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        logger.info(f"Query database for newest value of column '{value_type}' "
                    + "from table 'room-data', "
                    + "ordered by column 'datetime'.")
        last_val = cursor.execute(
            f"SELECT {value_type} FROM 'room-data' ORDER BY datetime DESC LIMIT 1"
        ).fetchone()[0]

    logger.info(f"Found last value from {value_type}: {last_val}")
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

    logger.info("Found max datetime: {}.".format(max_datetime))
    return max_datetime


def get_min_datetime():
    min_datetime = MIN_DATETIME
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()
        logger.info("Query database for min value of column 'datetime' from table 'room-data'.")
        min_datetime = pd.Timestamp(cursor.execute("SELECT MIN(datetime) FROM 'room-data'").fetchone()[0])

    logger.info("Found min datetime: {}.".format(min_datetime))
    return min_datetime


def get_day_temp():
    data = None
    max_datetime = get_max_datetime()
    query_datetime = max_datetime - timedelta(hours=24)

    with sqlite3.connect(
        DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        logger.info("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pd.read_sql(
            "SELECT datetime, temperature FROM 'room-data' WHERE datetime > ?",
            params=(query_datetime, ),
            parse_dates=['datetime'],
            con=connection
        )
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
        logger.info(f"Query database for {', '.join(values)} of the last 24 hours using pandas read_sql().")
        data = pd.read_sql(
            f"SELECT datetime, {', '.join(values)} FROM 'room-data' WHERE datetime > ?",
            params=(query_datetime, ),
            parse_dates=['datetime'],
            con=connection
        )
        logger.info("Successfully queried temperature data from the last 24hrs")
    return data


def get_temp_history(start_time, end_time):
    data = None

    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        logger.info("Query database for temperature-data of the last 24 hours using pandas read_sql().")
        data = pd.read_sql(
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
        res_df = pd.read_csv(filepath, encoding="UTF-16")
    except UnicodeError:
        res_df = pd.read_csv(filepath, encoding="UTF-8")
    # res_df.insert(0, dt, pandas.to_datetime(res_df['date'] + " " + res_df['time']))
    res_df.insert(
        0,
        dt,
        res_df.apply(lambda x: datetime.strptime(x['date'] + " " + x['time'], '%d-%m-%Y %H:%M:%S'), axis=1)
    )
    try:
        res_df = res_df.drop(columns=['date', 'time'])
    except ValueError:
        res_df = res_df.drop(['date', 'time'], axis=1)
    res_df['pressure'] = 0
    print(res_df)

    with sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
        res_df.to_sql('room', con=conn, index=False, index_label=dt, if_exists='append')


def add_room_data_to_db(date_time, temperature, humidity, brightness, pressure):
    with sqlite3.connect(DATABASE) as connection:

        # insert developer detail
        insert_with_param = "INSERT INTO 'room-data' "
        insert_with_param += "('datetime', 'temperature', 'humidity', 'brightness', 'pressure') "
        insert_with_param += "VALUES (?, ?, ?, ?, ?);"
        data_tuple = (date_time, temperature, humidity, brightness, pressure)

        cursor = connection.cursor()
        cursor.execute(insert_with_param, data_tuple)
        connection.commit()
        logger.info("Room Data added successfully.")


def add_mqtt_to_db(date_time, topic, message):
    with sqlite3.connect(DATABASE) as connection:
        # insert developer detail
        insert_with_param = "INSERT INTO 'mqtt_messages' "
        insert_with_param += "('datetime', 'topic', 'payload') "
        insert_with_param += "VALUES (?, ?, ?);"

        data_tuple = (date_time, topic, message)

        cursor = connection.cursor()
        cursor.execute(insert_with_param, data_tuple)
        connection.commit()
        logger.info("MQTT-Message '%s' added successfully to database.", message)


def get_mqtt_messages():
    data = None
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        logger.info("Query database for all mqtt messages using pandas read_sql().")
        data = pd.read_sql(
            "SELECT * FROM 'mqtt_messages' ORDER BY datetime DESC LIMIT 100;",
            parse_dates=['datetime'],
            con=connection
        )
        logger.info("Successfully queried mqtt messages.")
    return data


def get_mqtt_messages_by_topic(topics, limit=5000):
    data = None
    if topics:
        with sqlite3.connect(
                DATABASE,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as connection:
            logger.info("Query database for all mqtt messages using pandas read_sql().")
            data = pd.read_sql(
                "SELECT * FROM 'mqtt_messages' WHERE topic = {} ORDER BY datetime DESC LIMIT {};".format(
                    ' or topic = '.join(['?' for _ in topics]),
                    limit
                ),
                parse_dates=['datetime'],
                con=connection,
                params=topics,
            )
            logger.info("Successfully queried mqtt messages.")
    return data


def get_mqtt_topics():
    topics = None
    with sqlite3.connect(DATABASE) as connection:
        logger.info("Query database all recorded mqtt topics using pandas read_sql().")
        topics = pd.read_sql(
            "SELECT distinct topic FROM 'mqtt_messages';",
            con=connection
        )
        logger.debug("Successfully queried mqtt messages.")
    return topics.topic


def add_probe_request(time, mac, make, ssid, ssid_uppercase, rssi):
    with sqlite3.connect(DATABASE) as connection:
        insert_with_param = "INSERT INTO 'probe-request' "
        insert_with_param += "('datetime', 'macaddress', 'make', 'ssid', 'ssid_uppercase', 'rssi') "
        insert_with_param += "VALUES (?, ?, ?, ?, ?, ?);"
        data_tuple = (time, mac, make, ssid, ssid_uppercase, rssi)

        cursor = connection.cursor()
        cursor.execute(insert_with_param, data_tuple)
        connection.commit()
        logger.info("Probe request added successfully.")


def add_shopping_list(shopping_list):
    logger.debug(f"Add shopping list to database 'shopping': {shopping_list.to_dict()}")
    with sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        shopping_list.to_sql('shopping', connection, if_exists='append', index=False)
        logger.info("Shopping list added successfully.")


def get_unique_shopping_days():
    logger.debug("Get unique days in table 'shopping'.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        days = pd.read_sql(
            "SELECT DISTINCT Date FROM 'shopping' ORDER BY DATE",
            parse_dates=['Date'],
            con=connection
        )
        days = days.set_index('Date')
    return days


def get_unique_shopping_shops():
    logger.debug("Get unique Shops from table 'shopping'.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        shops = pd.read_sql(
            "SELECT DISTINCT Shop FROM 'shopping'",
            con=connection
        )
    return shops


def get_unique_shopping_items():
    logger.debug("Get unique Products from table 'shopping'.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        items = pd.read_sql(
            "SELECT DISTINCT Product FROM 'shopping'",
            con=connection
        )
    return items


def get_day_shop_expenses(day, shop):
    logger.debug(f"Get expenses for day {day} and shop {shop}.")
    day_str = day.strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        expense = pd.read_sql_query(
            "SELECT  sum(DISTINCT Payment) FROM 'shopping' WHERE Date = ? and Shop = ?;",
            params=(day_str, shop),
            con=connection
        )
    return expense.iloc[0, 0]


def get_shopping_expenses_per_shop(shop):
    logger.debug(f"Get expenses for shop {shop} from 'shopping' table.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        expense = pd.read_sql_query(
            "SELECT DISTINCT Date, Payment FROM 'shopping' WHERE Shop = ?;",
            params=(shop, ),
            parse_dates=['Date'],
            con=connection
        )
    expense_gouped = expense.groupby('Date')['Payment'].sum().rename(shop)
    return expense_gouped


def get_shopping_expenses_by_date(start, end=None):
    logger.debug(f"Get expenses from 'shopping' table between {start} and {end}.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        data = pd.read_sql(
            "SELECT DISTINCT Date, Payment FROM 'shopping' WHERE Date BETWEEN ? AND ? ORDER BY Date;",
            con=connection,
            parse_dates=['Date'],
            params=(start, end if end else datetime.now())
        )
    return data.groupby('Date').sum().reset_index()


def get_shopping_complete():
    """ Collects all entries from shopping table.
        Usage not advisable, since this can take a while.
    """
    logging.debug("Get complete 'shopping' table.")
    with sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    ) as connection:
        data = pd.read_sql(
            "SELECT * FROM 'shopping'",
            con=connection
        )
    return data


def get_gauge_data(value_type):
    if value_type not in VALUE_TYPES:
        raise ValueError(f"Invalid value '{value_type}'. Expected one of: {VALUE_TYPES}")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        logger.info(
            f"Query database for gauge data (min, max and last value) of column {value_type} from table 'room-data'."
        )
        min_val = cursor.execute(f"SELECT MIN({value_type}) FROM 'room-data'").fetchone()[0]
        max_val = cursor.execute(f"SELECT MAX({value_type}) FROM 'room-data'").fetchone()[0]
        curr_val = cursor.execute(f"SELECT {value_type} FROM 'room-data' ORDER BY datetime DESC LIMIT 1").fetchone()[0]
    return min_val, max_val, curr_val


def add_rf_data_to_db(curr_time, decimal, length, binary, pulse_length, protocol):
    with sqlite3.connect(DATABASE) as connection:

        # insert developer detail
        insert_with_param = "INSERT INTO 'rf-data' "
        insert_with_param += "(datetime, decimal, bits, binary, pulse_length, protocol) "
        insert_with_param += "VALUES (?, ?, ?, ?, ?, ?);"
        data_tuple = (curr_time, decimal, length, binary, pulse_length, protocol)

        cursor = connection.cursor()
        cursor.execute(insert_with_param, data_tuple)
        connection.commit()
        logger.info("Rf Data added successfully.")


def log_to_db():
    import os
    f = '/home/pi/log/'
    file = os.listdir(f)
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
