#!/usr/bin/env python3
# coding=utf-8

import time
import logging
import socket
import json
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

import sql_data
import rf_handler
import detached

logging.basicConfig(
    level=logging.DEBUG,
    format="%(module)s - %(levelname)s : %(message)s",
)
logger = logging.getLogger('mqtt_handler')
IS_CHARGING = False
TOPIC_ROOM_COMMAND = "room/control/command"
COMPUTER_STATUS = ""


def on_connect(client, userdata, flags, rc):
    topic = '#'
    client.subscribe(topic)
    logger.debug("'on_connect' called.")
    logger.info(f"Subscribed to topic '{topic}'.")


def on_message(client, userdata, msg):
    global COMPUTER_STATUS, IS_CHARGING
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    logger.debug(f"'on_message' called: topic='{topic}', msg='{payload}'.")

    if topic == 'trash':
        logger.info("Message is trash. Discarding")
    else:
        sql_data.add_mqtt_to_db(datetime.now(), topic, payload)

    if topic == "room/data":
        logger.info("Room data recieved. Write into database.")
        temp_message_to_db(payload)

    elif topic == "room/data/rf/recieve":
        logger.info("433Hz transmission recieved. Writing into database.")
        handle_rf_transmission(payload)

    elif topic == "tablet/shield/battery":
        logger.info("Tablet battery status recieved. Write to db and handle Battery.")
        handle_battery_level(payload)

    elif topic == "mqtt/probes":
        logger.info("Mqtt Probe recieved. Writing into database.")
        handle_probes(payload)

    elif topic.startswith(TOPIC_ROOM_COMMAND):
        logger.info("Room control message recieved.")
        handle_room_control(topic, payload)

    elif topic == "room/control/computer":
        logger.info("Computer control message recieved.")
        #thread = threading.Thread(target=handle_computer_state, args=(payload, ))
        #thread.start()
        handle_computer_state(payload)

    elif topic == "mqtt/computer/status":
        logger.info("Computer status message recieved.")
        COMPUTER_STATUS = payload

    else:
        logger.info(f"No rule for topic '{topic}'.")


def temp_message_to_db(payload):
    curr_time = datetime.now()

    room_data = json.loads(payload)
    for key, val in room_data.items():
        try:
            room_data[key] = float(val)
        except ValueError:
            logger.warning(f"Bad number in 'room/data' '{key}': '{val}'.")
            room_data[key] = 0

    sql_data.add_room_data_to_db(curr_time, room_data['temperature'], room_data['humidity'], 0, room_data['pressure'])


def handle_rf_transmission(payload):
    curr_time = datetime.now()
    rf_data = json.loads(payload)
    sql_data.add_rf_data_to_db(
        curr_time,
        rf_data['decimal'],
        rf_data['length'],
        rf_data['binary'],
        rf_data['pulse-length'],
        rf_data['protocol']
    )


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


def handle_room_control(topic, payload):
    command, socket_num = topic.rsplit('/', 1)
    if (
        command == f"{TOPIC_ROOM_COMMAND}/socket"
        and socket_num.isdigit()
        and int(socket_num) in rf_handler.CODES.keys()
    ):
        if payload in ['on', '1']:
            logger.info("Socket command detected. Turn socket '{rf_handler.CODES[socket_num].name}' on.")
            rf_handler.turn_socket_on(int(socket_num), "rpi_rf")
        elif payload in ['off', '0']:
            logger.info("Socket command detected. Turn socket '{rf_handler.CODES[socket_num].name}' off.")
            rf_handler.turn_socket_off(int(socket_num), "rpi_rf")
        else:
            logger.warning("Socket command detected but invalid command '{payload}'. Available: ['on', 'off', 0, 1].")
    else:
        logger.info("No route for this command.")


@detached.detachify
def handle_computer_state(payload):
    logger.debug(f"COMPUTER_STATUS={COMPUTER_STATUS}")
    if payload == 'on':
        if COMPUTER_STATUS == 'offline':
            logger.info("Turn computer on.")
            rf_handler.turn_socket_on(1, "rpi_rf")
            time.sleep(7)
            rf_handler.send_decimal(10000)
        else:
            logger.info("Computer is turned on. Doing nothing")
    else:
        logger.info("Turning computer off is currently unavaliable")


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

    while client:
        client.loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped through Keyboard Interrupt")
