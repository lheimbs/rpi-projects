#!/usr/bin/env python3
# coding=utf-8

#import os
import subprocess
import psutil
from psutil._common import bytes2human


def get_service_data(service):
    """ Call 'systemctl show [service]' and return the collected results in a dict """
    res = {
        'Names': '',
        'Description': '',
        'ExecMainPID': '',
        'ExecMainStatus': '',
        'ActiveState': '',
        'LoadState': '',
        'SubState': '',
        'UnitFileState': '',
        'ExecMainStartTimestamp': '',
        'ExecMainExitTimestamp': ''
    }
    try:
        key_value = subprocess.check_output(["systemctl","--user", "show", service],
                                            universal_newlines=True).split('\n')
    except subprocess.CalledProcessError as error:
        print(error.returncode, error.cmd, error.stdout, error.stderr)
        return {}
    except FileNotFoundError:
        print("Called command not found.")
        return {}

    for entry in key_value:
        key_val = entry.split("=", 1)
        if len(key_val) == 2 and key_val[0] in res.keys():
            res[key_val[0]] = key_val[1]
    return res


def get_cpu_percent():
    return psutil.cpu_percent()


def get_ram_data():
    ram = psutil.virtual_memory()
    return {
        'percent': ram.percent,
        'available': bytes2human(ram.available),
    }


def get_disk_data():
    disk = psutil.disk_usage('/')
    return {
        'percent': disk.percent,
        'available': bytes2human(disk.free),
    }


if __name__ == "__main__":
    import sys
    data = get_service_data(sys.argv[1])
    for key, value in data.items():
        print("{:40} : {:40}".format(key, value))
