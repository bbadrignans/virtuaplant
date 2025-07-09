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
    from modbus import (
        REG_RUN,
        REG_LEVEL,
        REG_CONTACT,
    )

from modbus import ClientModbus as Client
from modbus import ConnectionException

# Logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

client = Client("127.0.0.1", 1502)

try:
    client.connect()

    while True:
        client.write(REG_RUN, 1) 	    # Run Plant, Run!
        client.write(REG_LEVEL, 0) 	    # Level Sensor
        client.write(REG_CONTACT, 1) 	# Contact Sensor
        time.sleep(0.1)

except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print ("Unable to connect / Connection lost")
