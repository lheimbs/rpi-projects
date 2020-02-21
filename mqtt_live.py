#!/usr/bin/env python3
import unicodedata
from subprocess import Popen, PIPE, CalledProcessError

def sanitize_topic(topic):
    allowed_cats = ('Ll','Lu','Lo', 'Nd')
    allowed_chars = ('SOLIDUS', 'HYPHEN-MINUS', 'NUMBER SIGN')

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
            yield line#print(line, end='') # process line here

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)
