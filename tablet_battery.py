#!/home/pi/projects/rpi-projects/venv/bin/python3
# coding=utf-8

import logging
import paho.mqtt.client as mqtt

from rpi_rf import RFDevice

logging.basicConfig(
    filename='/home/pi/log/tablet_battery.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S'
)


GPIO_PIN = 4
TX_REPEAT = 10

RF_CODES = {
    "pc": { "on": 1131857, "off": 1131860},
    "tablet": {"on": 1134929, "off": 1134932},
    "other": {"on": 1135697, "off": 1135700},
}


def on_connect(client, userdata, flags, rc):
    logging.info("'on_connect' called.")
    client.subscribe("tablet/shield/battery")

def on_message(client, userdata, msg):
    level = msg.payload.decode("utf-8")
    logging.info("'on_message' called, msg='{}'".format(level))

    try:
        n_level = int(level)
    except ValueError:
        n_level = 0

    if n_level and n_level < 20:
        logging.info("Battery low detected. Turn Socket on.")
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 10
        rf_device.tx_code(RF_CODES['tablet']['on'])
        rf_device.cleanup()
    elif n_level and n_level > 80:
        logging.info("Battery high detected. Turn socket off.")
        rf_device = RFDevice(GPIO_PIN)
        rf_device.enable_tx()
        rf_device.tx_repeat = 10
        rf_device.tx_code(RF_CODES['tablet']['off'])
        rf_device.cleanup()                            
        
if __name__ == "__main__":   
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("192.168.1.201", 8883, 60)
    except:
        client.connect("192.168.1.205", 8883, 60)

    client.loop_start()

    while True:
        pass

