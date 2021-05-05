#!/usr/bin/env python3

import os
import re
import sys
import time
import argparse
import struct
import json
import socket
import logging
import subprocess
from threading import Timer

import pvporcupine
import pyaudio
import paho.mqtt.client as mqtt
from vosk import Model, KaldiRecognizer

# sys.path.append('/home/pi/projects/rpi-projects')
# import socketctl
from pixels import Pixels
from led_patterns import LedPattern

logger = logging.getLogger(__name__)

FPB = 8000
CHANNELS = 1
RATE = 16000
FORMAT = pyaudio.paInt16
SEARCH_WORDS = (
    "turn computer socket one two three four five turn on off "
    "start shutdown exit coffee make set timer cancel"
)
MQTT_DEVICE_NAME = "terminator"
MQTT_INFO_TOPIC = f"mqtt/{MQTT_DEVICE_NAME}/commands"
MQTT_TOPIC = "room/control/command"
MQTT_STATUS_TOPIC = f"mqtt/{MQTT_DEVICE_NAME}/status"
MQTT_INFO_TOPIC = f"mqtt/{MQTT_DEVICE_NAME}/command"

NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
SOCKET_COMMANDS_REGEX = [
    rf"turn (?P<command>on|off) socket (?P<socket_nr>{'|'.join(NUMBERS.keys())})",
    rf"turn socket (?P<socket_nr>{'|'.join(NUMBERS.keys())}) (?P<command>on|off)",
]
ONLINE_PUBLISH_TIMER = 900

pixels = None
porcupine = None
stream = None

pixels = Pixels()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", help="Path of model folder")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
        help="Enable debugging output. Takes precedence over -v/--verbose.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
        help="Increase verbosity.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    return args


def get_keyword_blocking(porcupine, pa, pixels):
    detected = False
    try:
        stream = pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=porcupine.sample_rate,
            frames_per_buffer=porcupine.frame_length,
            input=True,
        )

        logger.info("...waiting for keyword")
        while stream.is_active():
            pcm = stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            result = porcupine.process(pcm)
            if result >= 0:
                pixels.alexa_wakeup()
                logger.debug("keyword detected.")
                stream.stop_stream()
                detected = True

    finally:
        logger.debug("closing stream")
        stream.close()
        logger.debug("turning pixels off")
        time.sleep(1)
        pixels.off()
    return detected


def get_command_blocking(recognizer, pa, pixels):
    command = ""
    pixels.alexa_speak()
    try:
        stream = pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            frames_per_buffer=FPB,
            input=True,
        )

        logger.info("...waiting for command")

        while stream.is_active():
            pcm = stream.read(FPB)

            if recognizer.AcceptWaveform(pcm):
                result = json.loads(recognizer.Result())
                logger.debug(f"Result: '{result}'.")
                stream.stop_stream()
                command = result["text"]

    finally:
        logger.debug("closing stream")
        stream.close()
        pixels.off()

    return command


def connect(client):
    brokers = ["localhost"]
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
                logger.warning(
                    "Connection to broker failed. Hostname is probably not valid."
                )
            except TimeoutError:
                logger.warning("Connecting to broker timed out.")
    else:
        logger.error("Could not connect to broker.")
        return None
    return client


def on_mqtt_connect(client, userdata, flags, rc):
    logger.debug(f"Connected with result code {rc}.")
    client.publish(MQTT_STATUS_TOPIC, payload="online", qos=0)


def coffee_alarm(pixels):
    logger.info("Coffe alarm called!")
    pixels.put(pixels.pattern.alarm)
    time.sleep(5)
    pixels.off()


def socketctl(socket_nr, cmd):
    try:
        proc = subprocess.run(
            ["/home/pi/projects/rpi-projects/socketctl.py", cmd, str(socket_nr)]
        )
        logger.debug(
            "Socketctl {} {} returned {}...".format(socket_nr, cmd, proc.returncode)
        )
    except FileNotFoundError:
        logger.exception("Socketctl failed.")


#############################
#  VOICE COMMANDS           #
#############################
def coffee_timer():
    pixels.put(pixels.pattern.cmd_accepted)
    logger.info("Setting coffee timer for 4 minutes")

    def f():
        pixels.pattern.timer(4 * 60)

    pixels.put(f)
    time.sleep(4 * 60)
    # coffee_alarm(pixels)
    pixels.put(pixels.pattern.alarm)


def computer_control(command, client):
    cmd = command.replace("turn computer", "").strip()
    if cmd == "on" or cmd == "off":
        pixels.put(pixels.pattern.cmd_accepted)
        logger.info("Computer {} message detected.".format(cmd))
        # socketctl.socket_command(1, cmd)
        socketctl(1, cmd)
        client.publish("room/control/computer", cmd)
    else:
        pixels.put(pixels.pattern.cmd_rejected)
        logger.info("Computer on message badly formed.")


def socket_control(command, client):
    for command_re in SOCKET_COMMANDS_REGEX:
        m = re.match(command_re, command)
        if m:
            socket_nr = NUMBERS[m.group("socket_nr")]
            cmd = m.group("command")
            # socketctl.socket_command(socket_nr, cmd)
            socketctl(socket_nr, cmd)
            client.publish(f"{MQTT_TOPIC}/socket/{socket_nr}", cmd)
            return True
    return False


def main():
    keep_running = True
    args = get_args()

    pixels.pattern = LedPattern(show=pixels.show)

    client = mqtt.Client()
    client.on_connect = on_mqtt_connect
    client = connect(client)

    if args.model and os.path.exists(args.model):
        logger.debug("Using supplied model path.")
        model_path = args.model
    else:
        logger.warning(
            "Please supply a valid model path or download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md, unpack it and supply the folder path."
        )
        sys.exit(1)

    try:
        pa = pyaudio.PyAudio()

        porcupine = pvporcupine.create(keywords=["terminator", "blueberry"])

        model = Model(model_path)
        recognizer = KaldiRecognizer(model, 16000, SEARCH_WORDS)
        pixels.put(pixels.pattern.cmd_accepted)

        client.loop_start()
        start_time = time.time()
        while keep_running:
            # publish online status every hour
            if time.time() - start_time > ONLINE_PUBLISH_TIMER:
                client.publish(MQTT_STATUS_TOPIC, payload="online", qos=0, retain=False)
                start_time = time.time()

            # handle voice commands
            if get_keyword_blocking(porcupine, pa, pixels):
                command = get_command_blocking(recognizer, pa, pixels)

                logger.info(f"Recognized command: '{command}'.")
                client.publish(MQTT_INFO_TOPIC, payload=command, qos=1)

                if command == "exit":
                    logging.info("Exiting app.")
                    keep_running = False
                elif command == "set coffee timer" or command == "make coffee":
                    coffee_timer()

                elif command.startswith("turn computer"):
                    computer_control(command, client)

                elif socket_control(command, client):
                    pixels.put(pixels.pattern.cmd_accepted)

                else:
                    pixels.put(pixels.pattern.cmd_rejected)

    except KeyboardInterrupt:
        logging.info("stopping...")
    finally:
        if porcupine is not None:
            porcupine.delete()

        if pa is not None:
            pa.terminate()

        client.loop_stop()
        client.publish(MQTT_STATUS_TOPIC, payload="offline", qos=0)
        client.disconnect()


if __name__ == "__main__":
    main()
