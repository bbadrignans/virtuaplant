#!/usr/bin/env python

import sys
import tkinter as tk
from tkinter import ttk
from modbus import ClientModbus as Client
from modbus import ConnectionException
import os
import time
import json
import argparse

from modbus import (
    REG_RUN,
    REG_LEVEL,
    REG_CONTACT,
    REG_MOTOR_EN,
    REG_MOTOR_SPEED,
    REG_NOZZLE,
    REG_THROUGHPUT,
    REG_COLOR,
    MODBUS_PORT,
)
from modbus import COLORS

# Constants
HMI_SCREEN_WIDTH    = 23
HMI_SLEEP           = 200 #ms

class HMIWindow:
    def resetLabels(self):
        self.bottlePositionValue.config(text="N/A", fg="gray33")
        self.motorStatusValue.config(text="N/A", fg="gray33")
        self.levelHitValue.config(text="N/A", fg="gray33")
        self.processStatusValue.config(text="N/A", fg="gray33")
        self.nozzleStatusValue.config(text="N/A", fg="gray33")
        self.connectionStatusValue.config(text="OFFLINE", fg="red")

    def __init__(self, address, port):

        self.client = Client(address, port)
        self.client.connect()

        self.throughput = 1
        self.speed = 1
        self.color = ""

        self.window = tk.Tk()
        self.window.title("Bottle-filling factory - HMI - VirtuaPlant")

        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=HMI_SCREEN_WIDTH, pady=HMI_SCREEN_WIDTH)

        self.create_widgets()
        self.window.after(HMI_SLEEP, self.update_status)

    def create_widgets(self):
        row = 0

        status = tk.Label(self.frame, text="Status", font=("Helvetica", 14, "bold"))
        status.grid(row=row, column=0, columnspan=3)
        row +=1

        self.processStatusLabel = tk.Label(self.frame, text="Process Status")
        self.processStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.processStatusLabel.grid(row=row, column=0)
        self.processStatusValue.grid(row=row, column=1)
        row +=1

        self.bottlePositionLabel = tk.Label(self.frame, text="Bottle in position")
        self.bottlePositionValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.bottlePositionLabel.grid(row=row, column=0)
        self.bottlePositionValue.grid(row=row, column=1)
        row +=1

        self.levelHitLabel = tk.Label(self.frame, text="Level Hit")
        self.levelHitValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.levelHitLabel.grid(row=row, column=0)
        self.levelHitValue.grid(row=row, column=1)
        row +=1

        self.motorStatusLabel = tk.Label(self.frame, text="Motor Status")
        self.motorStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.motorStatusLabel.grid(row=row, column=0)
        self.motorStatusValue.grid(row=row, column=1)
        row +=1

        self.nozzleStatusLabel = tk.Label(self.frame, text="Nozzle Status")
        self.nozzleStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.nozzleStatusLabel.grid(row=row, column=0)
        self.nozzleStatusValue.grid(row=row, column=1)
        row +=1

        self.spacer2 = tk.Label(self.frame, text="")
        self.spacer2.grid(row=row, column=0)
        row +=1

        status = tk.Label(self.frame, text="Settings", font=("Helvetica", 14, "bold"))
        status.grid(row=row, column=0, columnspan=3)
        row +=1

        self.throughputLabel = tk.Label(self.frame, text="Nozzle throughput")
        self.throughputSlider = tk.Scale(
                self.frame, 
                showvalue=False,
                from_=0, to=4, 
                orient='horizontal', 
                )
        self.throughputSlider.set(1)
        self.throughputLabel.grid(row=row, column=0)
        self.throughputSlider.grid(row=row, column=1)
        row +=1

        self.speedLabel = tk.Label(self.frame, text="Motor speed")
        self.speedSlider = tk.Scale(
                self.frame, 
                showvalue=False,
                from_=0, to=4, 
                orient='horizontal', 
                )
        self.speedSlider.set(1)
        self.speedLabel.grid(row=row, column=0)
        self.speedSlider.grid(row=row, column=1)
        row +=1

        self.colorLabel = tk.Label(self.frame, text="Color")
        self.colorComboBoxValue = tk.StringVar()
        self.colorComboBox = ttk.Combobox(self.frame, textvariable=self.colorComboBoxValue)
        self.colorComboBox.width = 10
        self.colorComboBox['values'] = COLORS
        self.colorComboBox['state'] = 'readonly'
        self.colorComboBox.set(COLORS[0])
        self.colorLabel.grid(row=row, column=0)
        self.colorComboBox.grid(row=row, column=1)
        row +=1

        self.runButton = tk.Button(self.frame, text="Run", command=lambda: self.setProcess(1))
        self.stopButton = tk.Button(self.frame, text="Stop", command=lambda: self.setProcess(0))
        self.runButton.grid(row=row, column=0)
        self.stopButton.grid(row=row, column=1)
        row +=1

        self.spacer3 = tk.Label(self.frame, text="")
        self.spacer3.grid(row=row, column=0)
        row +=1

        status = tk.Label(self.frame, text="Connection", font=("Helvetica", 14, "bold"))
        status.grid(row=row, column=0, columnspan=3)
        row +=1

        self.connectionStatusLabel = tk.Label(self.frame, text="Status")
        self.connectionStatusValue = tk.Label(self.frame, text="OFFLINE", fg="red")
        self.connectionStatusLabel.grid(row=row, column=0)
        self.connectionStatusValue.grid(row=row, column=1)
        row +=1

    def setProcess(self, data=None):
        try:
            self.client.write(REG_RUN, data)
        except:
            pass

    def update_status(self):
        try:
            if ( self.throughput != self.throughputSlider.get()):
                self.throughput = self.throughputSlider.get()
                self.client.write(REG_THROUGHPUT, self.throughput)

            if ( self.speed != self.speedSlider.get()):
                self.speed = self.speedSlider.get()
                self.client.write(REG_MOTOR_SPEED, self.speed)

            if ( self.color != self.colorComboBox.get()):
                self.color = self.colorComboBox.get()
                self.client.write(REG_COLOR, COLORS.index(self.color))

            regs = self.client.readln(0, 17)

            self.bottlePositionValue.config(
                text="YES" if regs[REG_CONTACT] == 1 else "NO",
                fg="green" if regs[REG_CONTACT] == 1 else "red"
            )

            self.levelHitValue.config(
                text="YES" if regs[REG_LEVEL] == 1 else "NO",
                fg="green" if regs[REG_LEVEL] == 1 else "red"
            )

            self.motorStatusValue.config(
                text="ON" if regs[REG_MOTOR_EN] == 1 else "OFF",
                fg="green" if regs[REG_MOTOR_EN] == 1 else "red"
            )

            self.nozzleStatusValue.config(
                text="OPEN" if regs[REG_NOZZLE] == 1 else "CLOSED",
                fg="green" if regs[REG_NOZZLE] == 1 else "red"
            )

            self.processStatusValue.config(
                text="RUNNING" if regs[REG_RUN] == 1 else "STOPPED",
                fg="green" if regs[REG_RUN] == 1 else "red"
            )

            self.throughputLabel.config(
                    text="Throughput =" + str(regs[REG_THROUGHPUT]),
                    fg="green" if regs[REG_THROUGHPUT] < 5 else "red")
            self.throughputSlider.set(regs[REG_THROUGHPUT])

            self.speedLabel.config(
                    text="Motor speed =" + str(regs[REG_MOTOR_SPEED]),
                    fg="green" if regs[REG_MOTOR_SPEED] < 5 else "red")
            self.speedSlider.set(regs[REG_MOTOR_SPEED])

            self.colorComboBox.set(COLORS[regs[REG_COLOR]])

            self.connectionStatusValue.config(text="ONLINE", fg="green")

        except ConnectionException:
            if not self.client.connect():
                self.resetLabels()
        except:
            raise
        finally:
            self.window.after(HMI_SLEEP, self.update_status)

def parse_arguments():
    parser = argparse.ArgumentParser(description="The HMI")
    parser.add_argument("-i", "--ip", required=False, help="Adresse IP du serveur", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, required=False, help="Port du serveur PLC", default=1502)
    return parser.parse_args()

def main():
    args = parse_arguments()
    hmi = HMIWindow(args.ip, args.port)
    hmi.window.mainloop()

if __name__ == "__main__":
    sys.exit(main())
