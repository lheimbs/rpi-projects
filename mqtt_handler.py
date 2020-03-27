#!/usr/bin/env python3
# coding=utf-8

import sys
import logging
import argparse
import socket
import json
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
IS_CHARGING = False

def on_connect(client, userdata, flags, rc):
    topic = '#'
    client.subscribe(topic)
    logger.debug("'on_connect' called.")
    logger.info(f"Subscribed to topic '{topic}'.")

def on_message(client, userdata, msg):
    topic = msg.topic 
    payload = msg.payload.decode("utf-8")

    logger.debug(f"'on_message' called, add message to db: topic='{topic}', msg='{payload}'.")
    sql_data.add_mqtt_to_db(datetime.now(), topic, payload)

    if topic == "room/data":
        logger.info("Room data recieved. Write into database.")
        try:
            temp_message_to_db(payload)
        except:
            logger.exception("Error writing room data to database.")
    elif topic == "tablet/shield/battery":
        logger.info("Tablet battery status recieved. Write to db and handle Battery.")
        
        try:
            handle_battery_level(payload)
        except:
            logger.exception("Error handling incoming battery message.")

    elif topic == "mqtt/probes":
        logger.info("Mqtt Probe recieved. Writing into database.")
        
        try: 
            handle_probes(payload)
        except:
            logger.exception("Error occured while handling probe request data.")
    else:
        logger.info(f"No rule for topic '{topic}'.")


def temp_message_to_db(payload):
    curr_time = datetime.now()

    if "temperature" in payload and "humidity" in payload and "pressure" in payload and "temperature=nan" not in payload and 'nan' not in payload:
        room_data = dict([value.split('=') for value in payload.split(',')])
        try:
            temp = str(float(room_data['temperature']) - 4)
        except:
            temp = room_data['temperature'] 
        sql_data.add_room_data_to_db(curr_time, temp, room_data['humidity'], 0, room_data['pressure'])


def handle_battery_level(payload):
    try:
        n_level = int(payload)
        logger.debug("Battery level detected: %d", n_level)
    except ValueError:
        n_level = 0 
        logger.debug("Message has no battery level.")

    if payload == "low" or (0 < n_level <= 20):
        logger.info("Battery low detected. Turn Socket on.")
        rf_handler.turn_socket_on(2, "rpi_rf")
    elif payload == "full" or n_level >= 80: 
        logger.info("Battery high detected. Turn socket off.")
        rf_handler.turn_socket_off(2, "rpi_rf")
    elif payload == 'charging':
        logger.debug("Set IS_CHARGING to 'True'.")
        IS_CHARGING = True
    elif payload == 'discharging':
        logger.debug("Set IS_CHARGING to 'False'.")
        IS_CHARGING = False


def handle_probes(payload):
    try:
        probe_request = json.loads(payload)
    except json.decoder.JSONDecodeError:
        logger.error("Badly formed payload could not get parsed by json-lib.")
        return

    sql_data.add_probe_request(
        datetime.fromisoformat(probe_request['time']),
        probe_request['macaddress'],
        probe_request['make'],
        probe_request['ssid'],
        probe_request['uppercaseSSID'],
        probe_request['rssi']
    )


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
