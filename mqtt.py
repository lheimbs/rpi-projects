#!/usr/bin/env python3
# coding=utf-8

import os
import traceback
from datetime import datetime
import paho.mqtt.client as mqtt
import sql_data

#from SQL import SQL

LOG_FILE = os.path.join(os.sep, 'home', 'pi', 'log', 'mqtt.log')

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("tablet/shield/battery")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        curr_time = datetime.now()
        sql_data.add_mqtt_to_db(curr_time, msg.topic, msg.payload.decode("utf-8") )
        print(msg.topic+" "+str(msg.payload))
    except:
        traceback.print_exc()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.201", 8883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_start()

while True:
    pass
