#!/usr/bin/env python3
# coding=utf-8

import sys
import logging
import argparse
import socket
import paho.mqtt.client as mqtt
from datetime import datetime

import sql_data

parser = argparse.ArgumentParser(__name__)
levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
parser.add_argument('--log-level', default='INFO', choices=levels)
options = parser.parse_args()

logging.basicConfig(level=options.log_level, 
                    format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
                    datefmt="%d.%m.%Y %H:%M:%S")

logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    client.subscribe("room/data")
    logger.debug("'on_connect' called.")
    logger.info("Subscribed to topic 'room/data'.")

def on_message(client, userdata, msg):
    logger.debug("'on_message' called, msg='%s'", str(msg))
    try:
        temp_message_to_db(msg)
    except:
        logger.exception("Error wrinting incoming message to mqtt database.")

    payload = msg.payload.decode("utf-8")
        


def temp_message_to_db(msg):
    curr_time = datetime.now()
    payload = msg.payload.decode("utf-8")
    sql_data.add_mqtt_to_db(curr_time, msg.topic, payload)

    if "temperature" in payload and "humidity" in payload and "pressure" in payload and "temperature=nan" not in payload and 'nan' not in payload:
        room_data = dict([value.split('=') for value in payload.split(',')])
        try:
            temp = str(float(room_data['temperature']) - 4)
        except:
            temp = room_data['temperature'] 
        sql_data.add_room_data_to_db(curr_time, temp, room_data['humidity'], 0, room_data['pressure'])
    logger.debug("%s: %s", msg.topic, payload)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # connect to broker
    brokers = ['localhost', 'lennyspi.local', '192.168.1.201', '192.168.1.205']
    for host in brokers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sock.connect_ex((host, 8883)) == 0:
            client.connect(host, 8883, 60)
            logger.info(f"Connected to broker on host {host}.")
            break
    else:
        logger.error("Could not connect to broker.")
        sys.exit(1)

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
