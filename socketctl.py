#!/usr/bin/env python3

import sys
import time
import logging
import argparse
import subprocess

from rpi_rf import RFDevice

logger = logging.getLogger(__name__)

GPIO_PIN = 22
CODES = {
    1: {"name": "pc", "on": 1131857, "off": 1131860},
    2: {"name": "light", "on": 1134929, "off": 1134932},
    3: {"name": "rpi", "on": 1135697, "off": 1135700},
    4: {"name": "tablet", "on": 1135889, "off": 1135892},
    5: {"name": "server", "on": 1135937, "off": 1135940},
}
CMDS = {'on': '1', 'off': '0'}
SEND_PATH = "/home/pi/utils/433Utils/RPi_utils/send"


def get_args():
    parser = argparse.ArgumentParser(description="Optional Socket Control")
    parser.add_argument('-d', '--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.WARNING, help="Enable debugging output. Takes precedence over -v/--verbose.")
    parser.add_argument('-v', '--verbose', action="store_const", dest="loglevel", const=logging.INFO, help="Increase verbosity.")
    parser.add_argument('cmd', help="Command for socket. Can be a decimal number or one of [on|off].")
    parser.add_argument('socket', default=0, type=int, nargs='?', help="Socket number thats being controlled.")
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logger.debug("Arguments: {}...".format(args))
    return args


def socket_command(socketnr: int, cmd: str) -> bool:
    if not cmd.isnumeric() and cmd not in CMDS:
        logger.error("Invalid command! Use either [on|off] or an integer number.")
        return False

    if cmd.isnumeric():
        logger.info("Send decimal code {}.".format(cmd))
        return send_decimal(int(cmd))

    if socketnr not in CODES.keys():
        logger.warning("Bad Socketnumber {}. Use one of {}.".format(socketnr, CODES.keys()))
        return False

    logger.info("Send command {} to socket {} using rpi_rf.".format(cmd, socketnr))
    return send_code(socketnr, cmd) & send_code(socketnr, cmd)


def send_code(socketnr, code):
    ret_val = True
    logger.debug("Sending '{}' to socket {} using rpi_rf (code {})".format(code, socketnr, CODES[socketnr][code]))
    try:
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 20
        rf_device.tx_code(CODES[socketnr][code], tx_pulselength=500)
    except:
        ret_val = False
        logger.exception("Error while sending code to socket using rpi_rf")
    finally:
        rf_device.cleanup()
    return ret_val


def send_decimal(code):
    ret_val = True
    logger.debug(f"'send_decimal' called. Sending code {code} using rpi_rf")
    try:
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 20
        rf_device.tx_code(code, tx_pulselength=500)
    except:
        ret_val = False
        logger.exception("Error while sending code to socket using rpi_rf")
    finally:
        rf_device.cleanup()
    return ret_val


def main():
    args = get_args()

    ret_val = socket_command(args.socket, args.cmd)
    sys.exit(not ret_val)


if __name__ == "__main__":
    main()
