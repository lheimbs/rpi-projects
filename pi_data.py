#!/usr/bin/env python3
# coding=utf-8

import subprocess
import psutil
import logging
from psutil._common import bytes2human


logging.basicConfig(
    level='DEBUG',
    format="%(asctime)s - %(module)s - %(levelname)s : %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_service_data(service, user=True):
    """ Call 'systemctl show [service]' and return the collected results in a dict """
    res = {
        # 'Names': '',
        # 'Description': '',
        # 'ExecMainPID': '',
        # 'ExecMainStatus': '',
        'ActiveState': '',
        'LoadState': '',
        'SubState': '',
        'UnitFileState': '',
        # 'ExecMainStartTimestamp': '',
        # 'ExecMainExitTimestamp': ''
    }
    systemctl = ["systemctl", "show", "--user", service] if user else ["systemctl", "show", service]
    systemctl.append("--property="+','.join([prop for prop in res.keys()]))
    logger.debug(f"Executing command '{' '.join(systemctl)}'.")

    try:
        status = subprocess.check_output(
            systemctl,
            universal_newlines=True
        )
        logger.debug(f"Output: '{' '.join(status.split())}'.")
    except subprocess.CalledProcessError as error:
        logger.error(error.returncode, error.cmd, error.stdout, error.stderr)
        return {}
    except FileNotFoundError:
        logger.error("Called command not found.")
        return {}

    return dict([entry.split('=') for entry in status.split()])


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
