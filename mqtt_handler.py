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

logging.basicConfig(
    level=options.log_level,
    format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
)

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
        temp_message_to_db(payload)
    elif topic == "tablet/shield/battery":
        logger.info("Tablet battery status recieved. Write to db and handle Battery.")
        handle_battery_level(payload)

    elif topic == "mqtt/probes":
        logger.info("Mqtt Probe recieved. Writing into database.")
        handle_probes(payload)
    else:
        logger.info(f"No rule for topic '{topic}'.")


def temp_message_to_db(payload):
    curr_time = datetime.now()

    if "temperature" in payload and "humidity" in payload and "pressure" in payload and 'nan' not in payload:
        room_data = dict([value.split('=') for value in payload.split(',')])
        try:
            temp = str(float(room_data['temperature']) - 4)
        except ValueError:
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


def connect(client):
    brokers = ['localhost', 'lennyspi.local', '192.168.1.201', '192.168.1.205']
    port = 8883
    for host in brokers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug(f"Try connection to broker {host} on port {port}.")
        if sock.connect_ex((host, port)) == 0:
            try:
                client.connect(host, port, 60)
                logger.info(f"Connected to broker on host {host}.")
                break
            except ConnectionRefusedError:
                logger.warning("Broker refused connection. Are host/port correct?")
            except socket.gaierror:
                logger.warning("Connection to broker failed. Hostname is probably not valid.")
            except TimeoutError:
                logger.warning("Connecting to broker timed out.")
    else:
        logger.error("Could not connect to broker.")
        return None
    return client


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # connect to broker
    client = connect(client)

    run = True
    while client:
        client.loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped through Keyboard Interrupt")
