#!/usr/bin/env python3
# coding=utf-8

import time
import traceback
import argparse
import logging
import bme280 # pypi: RPi.bme280
import smbus2
import sql_data

parser = argparse.ArgumentParser(__name__)
levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
parser.add_argument('--log-level', default='INFO', choices=levels)
options = parser.parse_args()

logging.basicConfig(level=options.log_level, 
        format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
                    datefmt="%d.%m.%Y %H:%M:%S")

logger = logging.getLogger("room_data_logger")

def main():
    ''' Read the sensor-data (temp/humidity/brightness) every 60s
        Write the data in the data.db database, table room-data
    '''
    logger.info("Script started. Log level: %s", options.log_level)

    bme_port = 1
    bme_address = 0x76
    bus = smbus2.SMBus(bme_port)
    calibration_params = bme280.load_calibration_params(bus, bme_address)
    start_time = time.time()
    logger.debug("Start Time: %s", start_time)
    while True:
        try:
            # get data from sensors
            data = bme280.sample(bus, bme_address, calibration_params)
            light = 0#ADC0832.getResult()
            logger.info("Successfully read data from bme280: %s", data)
        except:
            logger.exception("Error while reading data from bme280.")
        else:
            try:
                sql_data.add_room_data_to_db(
                    date_time=data.timestamp, 
                    temperature=data.temperature, 
                    humidity=data.humidity, 
                    pressure=data.pressure, 
                    brightness=light)
                logger.info("Successfully added recorded date to database")
            except:
                logger.exception("Error writing Data into database.")

        # get exactly one reading all 60s
        now_time = time.time()
        logger.debug("Time at end of loop: %s. Sleeping now for %d seconds.", 
                     now_time,
                     60.0 - ((now_time - start_time) % 60.0))
        time.sleep(60.0 - ((now_time - start_time) % 60.0))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Script Exit: KeyboardInterrupt")
    except Exception as e:
        logger.exception("Unexpected Error in script!")

