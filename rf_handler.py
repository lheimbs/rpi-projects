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
SEND_PATH = "/home/pi/utils/433Utils/RPi_utils/send"

logger = logging.getLogger(__name__)

def turn_socket_on(socketnr, method):
    if socketnr not in CODES.keys():
        logger.warning("Wrong Socketnumber.")
        return False

    if method == "subprocess":
        logger.info("Turn Socket %d on using subprocess.", socketnr)
        res = subprocess.run([SEND_PATH, "10100", "{}".format(socketnr), "1"])
    elif method == "rpi_rf":
        logger.info("Turn Socket %d on using rpi_rf.", socketnr)
        send_code(socketnr, 'on')
    else:
        logger.warning("Wrong method.")
        return False
    return True


def turn_socket_off(socketnr, method="rpi_rf"):
    if socketnr not in CODES.keys():
        logger.warning("Wrong Socketnumber.")
        return False

    if method == "subprocess":
        logger.info("Turn Socket {} off using subprocess.".format(CODES[socketnr]["name"]))
        res = subprocess.run([SEND_PATH, "10100", "{}".format(socketnr), "0"])
    elif method == "rpi_rf":
        logger.info("Turn Socket %d on using Python method.", socketnr)
        send_code(socketnr, 'off')
    else:
        logger.warning("Wrong method")
        return False
    return True


def send_code(socketnr, code):
    logger.debug("'send_code' called. Sending code %s to socket %d using rpi_rf", code, socketnr)
    try:
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 10
        rf_device.tx_code(CODES[socketnr][code])
    except:
        logger.exception("Error while sending code to socket using rpi_rf")
    finally:
        rf_device.cleanup()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    turn_socket_on(3, "subprocess")
    time.sleep(2)
    turn_socket_off(3, "subprocess")
    time.sleep(2)
    turn_socket_on(3, "rpi_rf")
    time.sleep(2)
    turn_socket_off(3, "rpi_rf")
