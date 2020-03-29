#!/usr/bin/env python3

import logging
from pystemd.systemd1 import Unit

logger = logging.getLogger(__name__)


def get_service_info(service):
    # state info ['ActiveState', 'LoadState', 'LoadError', 'SubState', 'UnitFileState']
    # use systemctl --state=help
    unit = Unit(f"{service.encode()}.service", _autoload=True)
    load_state = unit.Unit.LoadState.decode('utf-8')
    active_state = unit.Unit.ActiveState.decode('utf-8')

    if load_state == 'loaded':
        logger.debug(f"Service file for '{service}' is loaded.")
        loaded = True
    elif load_state == 'not-found':
        logger.warning(f"Service file for '{service}' not found.")
        loaded = False
    elif load_state == 'bad-setting':
        logger.warning(f"Bad setting in service file for '{service}'.")
        loaded = False
    else:
        logger.warning(
            f"Unknown status of service file for '{service}': '{load_state}'."
        )
        loaded = False

    if active_state == 'active':
        logger.debug(f"Service '{service}' is avtive.")
        activated = True
    elif active_state == 'inactive':
        logger.warning(f"Service '{service}' is inactive.")
        activated = False
    elif active_state == 'failed':
        logger.warning(f"Service '{service}' has failed.")
        activated = False
    else:
        logger.warning(
            f"Unknown status of service '{service}': '{active_state}'."
        )
        activated = False

    return loaded, activated
