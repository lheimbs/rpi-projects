#!/usr/bin/env python3
# coding=utf-8

import time
import datetime
import os
import traceback
import subprocess
import argparse
import csv
import shutil
import bme280 # pypi: RPi.bme280
import smbus2
import ADC0832
import sql_data

FILE_FOLDER = os.path.join(os.sep, 'home', 'pi', 'log')
RESULT_FILE = 'results.csv'
LOG_FILE = 'data_logger.log'

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                help="increase output verbosity")
VERBOSITY = ap.parse_args().verbosity

def log(logstring):
    ''' Loggin utility:
        0: only print to console
        1: only print to logfile
        2: print to both console and logfile
    '''
    if VERBOSITY == 0:
        print("[LOG] " + logstring)
    elif VERBOSITY == 1:
        with open(os.path.join(FILE_FOLDER, LOG_FILE), 'a+') as logfile:
            curr_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            logfile.write(curr_time + ":   " + str(logstring) + "\n")
    elif VERBOSITY == 2:
        print("[LOG] " + logstring)
        with open(os.path.join(FILE_FOLDER, LOG_FILE), 'a+') as logfile:
            curr_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            logfile.write(curr_time + ":   " + str(logstring) + "\n")

def init():
    log("Script started")
    week = 0
    log_file_path = os.path.join(FILE_FOLDER, RESULT_FILE)
    # Setup the photoresistor
    ADC0832.setup()

    if not os.path.exists(log_file_path):
        log("'{}' does not exist. Creating it new.".format(log_file_path))
        with open(log_file_path, 'w', encoding='UTF-16') as logfile:
            logfile.write("date,time,temperature,humidity,brighness\n")

    with open(log_file_path, 'r', encoding="UTF-16") as file:
        for row in reversed(list(csv.reader(file))):
            if "date" in row:
                week=0
            else:
                date=datetime.datetime.strptime(row[0] + ' ' + row[1], '%d-%m-%Y %H:%M:%S')
                week = date.isocalendar()[1]
                break 
    return week

def weekly_res_file(old_week):
    ''' If a new week has been detected, save current results.csv as week-xx-results.csv
        and begin with a new clean results.csv for the new week 
    '''
    date = datetime.datetime.now()
    week = date.isocalendar()[1]

    if old_week == 0:
        return week
    elif week > old_week or week < old_week:
        log("Week has changed. Old Week: {}. New Week: {}".format(old_week, week))
        res_save_name = "week-" + str(old_week) + "-results.csv"
        shutil.copy2(os.path.join(FILE_FOLDER, RESULT_FILE), os.path.join(FILE_FOLDER, res_save_name))

        with open(os.path.join(FILE_FOLDER, RESULT_FILE), 'w', encoding='UTF-16') as resfile:
            resfile.write("date,time,temperature,humidity,brighness\n")
        return week
    else:
        return old_week

def write_to_file(res_string):
    ''' Write results to RESULTS_FILE '''
    with open(os.path.join(FILE_FOLDER, RESULT_FILE), 'a+', encoding='UTF-16') as file:
        file.write(res_string)

def main():
    ''' Read the sensor-data (temp/humidity/brightness) every 60s
        Write the data into a results file
        Results files hold the data of one week
    '''
    bme_port = 1
    bme_address = 0x76
    bus = smbus2.SMBus(bme_port)
    current_week=init()
    start_time = time.time()
    #sql = SQL.SQL('/home/pi/data/data.db', 'room_data')
    while True:

        # if a new week has begun, backup last week and begin with a clean res file
        current_week = weekly_res_file(current_week)

        # get data from sensors
        data = bme280.sample(bus, bme_address)
        light = ADC0832.getResult()

        # get the current date for logging
        curr_datetime = datetime.datetime.now()
        curr_date = curr_datetime.strftime('%d-%m-%Y')
        curr_time = curr_datetime.strftime('%H:%M:%S')

        #sql.add_data_to_db(curr_date + " " + curr_time, data.temperature, data.humidity, light)
        write_to_file("%s,%s,%4f,%4f,%d\n" % (curr_date, curr_time, data.temperature, data.humidity, light))
        sql_data.add_to_db(date_time=data.timestamp, temperature=data.temperature, humidity=data.humidity, pressure=data.pressure, brightness=light)

        # get exactly one reading all 60s
        now_time = time.time()
        time.sleep(60.0 - ((now_time - start_time) % 60.0))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("Script Exit: KeyboardInterrupt")
    except Exception as e:
        log("Script Exit: " + str(e))
        log(traceback.format_exc())
    finally:
        ADC0832.destroy()
