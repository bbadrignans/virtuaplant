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

REG_RUN         = 0x0
REG_MOTOR_EN    = 0x1
REG_MOTOR_SPEED = 0x2
REG_NOZZLE      = 0x3
REG_CONTACT     = 0x4
REG_LEVEL       = 0x5
REG_THROUGHPUT  = 0x6
REG_COLOR       = 0x7

COLORS = ["green", "red", "blue", "orange", "pink"]

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
    
    def write(self, addr, data):
        self.context[0x0].setValues(3, addr, [data])
    
    def read(self, addr):
        return self.context[0x0].getValues(3, addr, count=1)[0]

def main():
    log.setLevel(logging.INFO)
    log.info("Starting modbus server !")
    server = ServerModbus()
    server.start()
    return 0

if __name__ == "__main__":
    sys.exit(main())
