#!/usr/bin/env python3

import unicodedata
import logging
from datetime import datetime
from subprocess import Popen, PIPE, CalledProcessError


logging.basicConfig(level='DEBUG',
                    format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
                    datefmt="%d.%m.%Y %H:%M:%S")

logger = logging.getLogger(__name__)


def sanitize_topic(topic):
    allowed_cats = ('Ll', 'Lu', 'Lo', 'Nd')
    allowed_chars = ('SOLIDUS', 'HYPHEN-MINUS', 'NUMBER SIGN')

    if not topic:
        return False

    for curr_char in topic:
        cat = unicodedata.category(curr_char)
        if cat in allowed_cats:
            continue

        name = unicodedata.name(curr_char)
        if name in allowed_chars:
            continue

        # character is not whitelisted
        return False
    # all characters are whitelisted
    return True


def get_mqtt_live(topic):
    if not sanitize_topic(topic):
        return

    cmd = ['mosquitto_sub', '-h', 'localhost', '-p', '8883', '-t', topic, '-W', '60', '-F', '%j']
    with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            yield line  # print(line, end='') # process line here

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)


def mqtt_connect_async(client, queue):
    def on_connect(client, userdata, flags, rc):
        client.connected_flag = True
        logger.debug("'on_connect' called.")

    def on_message(client, userdata, msg):
        logger.debug(f"'on_message' called")        
        now = datetime.now()
        queue.append(
            {
                'date': now.strftime('%d.%m.%Y'),
                'time': now.strftime('%X'),
                'topic': msg.topic,
                'payload': msg.payload.decode('UTF-8'),
                'qos': msg.qos,
            }
        )

    def on_disconnect(client, userdata, rc):
        client.connected_flag = False
        if rc != 0:
            logger.debug("Unexpected disconnection.")

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("192.168.1.201", 8883, 60)
        logging.info("MQTT Broker at IP 192.168.1.201 found")
    except OSError:
        logger.warning("MQTT Broker is not running on 192.168.1.201. Trying *.205")
        try:
            client.connect("192.168.1.205", 8883, 60)
            logger.info("MQTT Broker at IP 192.168.1.205 found")
        except OSError:
            logger.error("No MQTT Broker running on known Ips.")
            return

    client.loop_start()