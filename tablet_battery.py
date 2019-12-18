#!/usr/bin/env python3
# coding=utf-8

import logging
import argparse
#import threading
import paho.mqtt.client as mqtt
from datetime import datetime

import sql_data
import rf_handler

parser = argparse.ArgumentParser(__name__)
levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
parser.add_argument('--log-level', default='INFO', choices=levels)
options = parser.parse_args()

logging.basicConfig(level=options.log_level, 
                    format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
                    datefmt="%d.%m.%Y %H:%M:%S")

logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    client.subscribe("tablet/shield/battery")
    logger.debug("'on_connect' called.")

def on_message(client, userdata, msg):
    logger.debug("'on_message' called, msg='%s'", str(msg))
    try:
        message_to_db(msg)
        handle_battery_level(msg)
        #threading.Thread(target=handle_battery_level, args=(msg,)).start()
    except:
        logger.exception("Error handling incoming message")

def handle_battery_level(msg):
    payload = msg.payload.decode("utf-8")

    try:
        n_level = int(payload)
    except ValueError:
        n_level = 0
    logger.debug("[handle_battery_level] n_level = %d", n_level)

    if payload == "low" or (0 < n_level <= 20):
        logger.info("Battery low detected. Turn Socket on.")
        rf_handler.turn_socket_on(2, "rpi_rf")
    elif payload == "high" or n_level >= 80:
        logger.info("Battery high detected. Turn socket off.")
        rf_handler.turn_socket_off(2, "subprocess")
        #rf_handler.turn_socket_off(2, "rpi_rf")

def message_to_db(msg):
    curr_time = datetime.now()
    payload = msg.payload.decode("utf-8")
    sql_data.add_mqtt_to_db(curr_time, msg.topic, payload)
    logger.debug("%s: %s", msg.topic, payload)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("192.168.1.201", 8883, 60)
        logging.info("MQTT Broker at IP 192.168.1.201 found")
    except:
        logger.warning("MQTT Broker is not running on 192.168.1.201. Trying *.205")
        try:
            client.connect("192.168.1.205", 8883, 60)
            logger.info("MQTT Broker at IP 192.168.1.205 found")
        except:
            logger.error("No MQTT Broker running on known Ips.")
            return

    #client.loop_start()
    run = True
    while run:
        client.loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped through Keyboard Interrupt")
    except:
        logger.exception("Unexpected Error during MQTT handling")
