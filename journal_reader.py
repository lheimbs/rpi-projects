import sys
import datetime
import select
import pprint
from systemd import journal
import asyncio


def get_user_service_log_day(service_name):
    reader = journal.Reader()
    reader.log_level(journal.LOG_INFO)
    reader.this_machine()
    reader.add_match(_SYSTEMD_USER_UNIT='service_name')

    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    reader.seek_realtime(yesterday)

    log = [(entry['__REALTIME_TIMESTAMP'], entry['MESSAGE']) for entry in reader]
    return log


def get_user_service_log_boot(service_name):
    reader = journal.Reader()
    reader.log_level(journal.LOG_INFO)
    reader.this_boot()
    reader.this_machine()

    reader.add_match(_SYSTEMD_USER_UNIT='service_name')

    log = [(entry['__REALTIME_TIMESTAMP'], entry['MESSAGE']) for entry in reader]
    return log


async def get_live_service_log(service_name, queue):
    reader = journal.Reader()
    reader.log_level(journal.LOG_INFO)
    reader.this_machine()
    reader.add_match(_SYSTEMD_USER_UNIT='service_name')

    reader.seek_realtime(datetime.datetime.today())

    p = select.poll()
    # Register the journal's file descriptor with the polling object.
    journal_fd = reader.fileno()
    poll_event_mask = reader.get_events()
    p.register(journal_fd, poll_event_mask)

    # Poll for new journal entries every 250ms
    while True:
        if p.poll(1000):
            if reader.process() == journal.APPEND:
                for entry in j:
                    queue.put_nowait((entry['__REALTIME_TIMESTAMP'], entry['MESSAGE']))
