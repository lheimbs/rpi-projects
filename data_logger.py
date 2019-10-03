#!/home/pi/projects/rpi-projects/venv/bin/python
# coding=utf-8

import time
import datetime
import os
import traceback
import subprocess
import argparse
import csv
import shutil
import bme280
import smbus2
import ADC0832


def init():
    print("Script started")
    # Setup the photoresistor
    ADC0832.setup()

def main():
    ''' Read the sensor-data (temp/humidity/brightness) every 60s
        Write the data into a results file
        Results files hold the data of one week
    '''
    bme_port = 1
    bme_address = 0x76
    bus = smbus2.SMBus(bme_port)
    start_time = time.time()
    while True:
        # get data from sensors
        data = bme280.sample(bus, bme_address)
        light = ADC0832.getResult()

        # get the current date for logging
        curr_datetime = datetime.datetime.now()

        # write to db

        # get exactly one reading all 60s
        now_time = time.time()
        time.sleep(60.0 - ((now_time - start_time) % 60.0))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Script Exit: KeyboardInterrupt")
    finally:
        ADC0832.destroy()
