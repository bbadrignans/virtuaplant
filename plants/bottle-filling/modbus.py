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

logging.basicConfig()
log = logging.getLogger()

class ClientModbus(ModbusTcpClient):    
    def __init__(self, address, port=MODBUS_PORT):
        super().__init__(address, port)

    def read(self, addr):
        try:
            regs = self.readln(addr, 1)
            return regs[0]
        except ConnectionException:
            self.connect()
            regs = self.readln(addr, 1)
            return regs[0]

    def readln(self, addr, size):
        rr = self.read_holding_registers(addr, size)
        if not rr or not hasattr(rr, 'registers'):
            raise ConnectionException
        if len(rr.registers) < size:
            raise ConnectionException
        return rr.registers

    def write(self, addr, data):
        self.write_register(addr, data)

    def writeln(self, addr, data, size):
        self.write_registers(addr, data)

class ServerModbus:
    def __init__(self, address="localhost", port=MODBUS_PORT):
        self.address = address
        self.port = port
        self.allow_reuse_address = True
        self.run = 1
        self.motor = 0
        self.nozzle = 0
        self.contact = 0
        self.level_sensor = 0
        self.block = ModbusSequentialDataBlock(0x00, [0]*0x3ff)
        store = ModbusSlaveContext(di=self.block, co=self.block, hr=self.block, ir=self.block)
        self.context = ModbusServerContext(slaves=store, single=True)
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = 'MockPLCs'
        self.identity.ProductCode = 'MP'
        self.identity.VendorUrl = 'http://github.com/bashwork/pyddmodbus/'
        self.identity.ProductName = 'MockPLC 3000'
        self.identity.ModelName = 'MockPLC Ultimate'
        self.identity.MajorMinorRevision = '1.0'

    def read(self, addr):
        if ( addr == 0 ):
            return self.run
        if ( addr == 1 ):
            return self.level_sensor
        if ( addr == 2 ):
            return self.contact
        if ( addr == 3 ):
            return self.motor
        if ( addr == 4 ):
            return self.nozzle
        else:
            return 0

    def write(self, addr, value):
        log.info("Write !")
        if ( addr == 0 ):
            log.info("Run !")
            self.setRun(value)
        if ( addr == 1 ):
            self.setLevelSensor(value)
        if ( addr == 2 ):
            self.setContact(value)
        if ( addr == 3 ):
            self.setMotor(value)
        if ( addr == 4 ):
            self.setNozzle(value)

    def start(self):
        StartTcpServer(context=self.context, identity=self.identity, address=(self.address, self.port))

    def setRun(self, value):
        self.run = value

    def setMotor(self, value):
        self.motor = value

    def setNozzle(self, value):
        self.nozzle = value

    def setContact(self, value):
        self.contact = value

    def setLevelSensor(self, value):
        self.level_sensor = value

def main():
    log.setLevel(logging.INFO)
    log.info("Starting modbus server !")
    server = ServerModbus()
    server.start()
    return 0

if __name__ == "__main__":
    sys.exit(main())
