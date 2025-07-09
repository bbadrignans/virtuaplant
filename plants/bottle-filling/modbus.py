#!/usr/bin/env python

import sys
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
import logging

MODBUS_PORT = 1502

REG_RUN     = 0x0
REG_MOTOR   = 0x1
REG_NOZZLE  = 0x2
REG_CONTACT = 0x3
REG_LEVEL   = 0x4

logging.basicConfig()
log = logging.getLogger()

class ClientModbus(ModbusTcpClient):    
    def __init__(self, address, port=MODBUS_PORT):
        super().__init__(address, port)

    def read(self, addr):
        regs = self.readln(addr,1)

        return regs[0]

    def readln(self, addr, size):
        rr = self.read_holding_registers(addr,size)
        regs = []

        if not rr or not rr.registers:
            raise ConnectionException

        regs = rr.registers

        if not regs or len(regs) < size:
            raise ConnectionException

        return regs

    def write(self, addr, data):
        self.write_register(addr, data)

    def writeln(self, addr, data, size):
        self.write_registers(addr, data)

class ServerModbus:
    def __init__(self, address="localhost", port=MODBUS_PORT):

        self.address = address
        self.port = port

        self.block = ModbusSequentialDataBlock(0x00, [0]*20)
        self.store = ModbusSlaveContext(di=self.block, co=self.block, hr=self.block, ir=self.block)
        self.context = ModbusServerContext(slaves=self.store, single=True)

        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = 'MockPLCs'
        self.identity.ProductCode = 'MP'
        self.identity.VendorUrl = 'http://github.com/bashwork/pyddmodbus/'
        self.identity.ProductName = 'MockPLC 3000'
        self.identity.ModelName = 'MockPLC Ultimate'
        self.identity.MajorMinorRevision = '1.0'

    def start(self):
        StartTcpServer(context=self.context, identity=self.identity, address=(self.address, self.port))

    def setRun(self, value):
        self.store.setValues(3, REG_RUN, [value])

    def setMotor(self, value):
        self.store.setValues(3, REG_MOTOR, [value])

    def setNozzle(self, value):
        self.store.setValues(3, REG_NOZZLE, [value])

    def setContact(self, value):
        self.store.setValues(3, REG_CONTACT, [value])

    def setLevelSensor(self, value):
        self.store.setValues(3, REG_LEVEL, [value])

    def getRun(self):
        return self.store.getValues(3, REG_RUN)[0]

    def getMotor(self):
        return self.store.getValues(3, REG_MOTOR)[0]

    def getNozzle(self):
        return self.store.getValues(3, REG_NOZZLE)[0]

    def getContact(self):
        return self.store.getValues(3, REG_CONTACT)[0]

    def getLevelSensor(self):
        return self.store.getValues(3, REG_LEVEL)[0]

def main():
    log.setLevel(logging.INFO)
    log.info("Starting modbus server !")
    server = ServerModbus()
    server.start()
    return 0

if __name__ == "__main__":
    sys.exit(main())
