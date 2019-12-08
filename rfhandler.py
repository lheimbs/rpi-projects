#!/usr/bin/env python3

import time
import logging
import subprocess
from rpi_rf import RFDevice

GPIO_PIN = 4
CODES = {
    1: {"name": "pc",     "on": 1131857, "off": 1131860},
    2: {"name": "tablet", "on": 1134929, "off": 1134932},
    3: {"name": "other",  "on": 1135697, "off": 1135700},
}


def turn_socket_on(socketnr, method):
    if socketnr not in CODES.keys():
        logging.warning("Wrong Socketnumber.")
        return False

    if method == "subprocess":
        logging.info("Turn Socket {} on using subprocess.".format(CODES[socketnr]["name"]))
        res = subprocess.run(["/home/pi/Downloads/433Utils/RPi_utils/send", "10100", "{}".format(socketnr), "1"])

    elif method == "rpi_rf":
        logging.info("Turn Socket on using Python method.")
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 10
        rf_device.tx_code(CODES[socketnr]['on'])
        rf_device.cleanup()

    else:
        logging.warning("Wrong method.")
        return False
    return True


def turn_socket_off(socketnr, method):
    if socketnr not in CODES.keys():
        logging.warning("Wrong Socketnumber.")
        return False

    if method == "subprocess":
        logging.info("Turn Socket {} on using subprocess.".format(CODES[socketnr]["name"]))
        res = subprocess.run(["/home/pi/Downloads/433Utils/RPi_utils/send", "10100", "{}".format(socketnr), "0"])
                                                                                                                   
    elif method == "rpi_rf":
        logging.info("Turn Socket on using Python method.")
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 10
        rf_device.tx_code(CODES[socketnr]['off'])
        rf_device.cleanup()

    else:
        print("Wrong method")
        return False
    return True

if __name__ == "__main__":
    turn_socket_on(3, "subprocess")
    time.sleep(2)
    turn_socket_off(3, "subprocess")
    time.sleep(2)
    turn_socket_on(2, "rpi_rf")
    time.sleep(2)
    turn_socket_off(2, "rpi_rf")
