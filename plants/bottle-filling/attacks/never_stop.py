import logging
import time
import os
import sys
import json
import threading
import contextlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os

with open(os.devnull, 'w') as fnull, contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
    from world import (
        PLC_RW_ADDR,
        PLC_TAG_NEVER_STOP
    )

from modbus import ClientModbus as Client
from modbus import ConnectionException

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

PORTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'ports.json')
PORTS_FILE = os.path.abspath(PORTS_FILE)

while not os.path.exists(PORTS_FILE):
    print("En attente de world.py...")
    time.sleep(1)

with open(PORTS_FILE, "r") as f:
    ports = json.load(f)

client = Client("localhost", port=ports["plc"])
stop_flag = False

def listen_for_enter():
    input("")
    global stop_flag
    stop_flag = True

try:
    client.connect()

    threading.Thread(target=listen_for_enter, daemon=True).start()

    client.write(PLC_RW_ADDR + PLC_TAG_NEVER_STOP, 1)

    while not stop_flag:
        time.sleep(0.01)

    client.write(PLC_RW_ADDR + PLC_TAG_NEVER_STOP, 0)

except Exception as e:
    log.error(f"Erreur dans never_stop.py : {e}")
