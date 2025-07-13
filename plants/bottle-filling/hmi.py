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

from modbus import REG_CONTACT, REG_LEVEL, REG_MOTOR, REG_NOZZLE, REG_RUN, REG_THROUGHPUT, REG_COLOR
from modbus import COLORS

# Constants
HMI_SCREEN_WIDTH    = 40
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

        self.throughput = 2
        self.color = ""

        self.window = tk.Tk()
        self.window.title("Bottle-filling factory - HMI - VirtuaPlant")

        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=HMI_SCREEN_WIDTH, pady=HMI_SCREEN_WIDTH)

        self.create_widgets()
        self.window.after(HMI_SLEEP, self.update_status)

    def create_widgets(self):
        label = tk.Label(self.frame, text="Bottle-filling control HMI", font=("Helvetica", 16, "bold"))
        label.grid(row=0, column=0, columnspan=3)

        self.bottlePositionLabel = tk.Label(self.frame, text="Bottle in position")
        self.bottlePositionValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.bottlePositionLabel.grid(row=1, column=0)
        self.bottlePositionValue.grid(row=1, column=1)

        self.nozzleStatusLabel = tk.Label(self.frame, text="Nozzle Status")
        self.nozzleStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.nozzleStatusLabel.grid(row=2, column=0)
        self.nozzleStatusValue.grid(row=2, column=1)

        self.motorStatusLabel = tk.Label(self.frame, text="Motor Status")
        self.motorStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.motorStatusLabel.grid(row=3, column=0)
        self.motorStatusValue.grid(row=3, column=1)

        self.levelHitLabel = tk.Label(self.frame, text="Level Hit")
        self.levelHitValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.levelHitLabel.grid(row=4, column=0)
        self.levelHitValue.grid(row=4, column=1)

        self.processStatusLabel = tk.Label(self.frame, text="Process Status")
        self.processStatusValue = tk.Label(self.frame, text="N/A", fg="gray33")
        self.processStatusLabel.grid(row=5, column=0)
        self.processStatusValue.grid(row=5, column=1)

        self.connectionStatusLabel = tk.Label(self.frame, text="Connection Status")
        self.connectionStatusValue = tk.Label(self.frame, text="OFFLINE", fg="red")
        self.connectionStatusLabel.grid(row=6, column=0)
        self.connectionStatusValue.grid(row=6, column=1)

        self.throughputLabel = tk.Label(self.frame, text="Throughput")
        self.throughputSlider = tk.Scale(
                self.frame, 
                from_=0, to=4, 
                orient='horizontal', 
                )
        self.throughputSlider.set(2)
        self.throughputLabel.grid(row=7, column=0)
        self.throughputSlider.grid(row=7, column=1)

        self.colorLabel = tk.Label(self.frame, text="Color")
        self.colorComboBoxValue = tk.StringVar()
        self.colorComboBox = ttk.Combobox(self.frame, textvariable=self.colorComboBoxValue)
        self.colorComboBox['values'] = COLORS
        self.colorComboBox['state'] = 'readonly'
        self.colorComboBox.set(COLORS[0])
        self.colorLabel.grid(row=8, column=0)
        self.colorComboBox.grid(row=8, column=1)

        self.spacer1 = tk.Label(self.frame, text="")
        self.spacer2 = tk.Label(self.frame, text="")
        self.spacer1.grid(row=9, column=0)
        self.spacer2.grid(row=10, column=0)

        self.runButton = tk.Button(self.frame, text="Run", command=lambda: self.setProcess(1))
        self.stopButton = tk.Button(self.frame, text="Stop", command=lambda: self.setProcess(0))
        self.runButton.grid(row=11, column=0)
        self.stopButton.grid(row=11, column=1)

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

            if ( self.color != self.colorComboBox.get()):
                self.color = self.colorComboBox.get()
                self.client.write(REG_COLOR, COLORS.index(self.color))

            regs = self.client.readln(0, 17)

            self.bottlePositionValue.config(
                text="YES" if regs[REG_CONTACT] == 1 else "NO",
                fg="green" if regs[REG_CONTACT] == 1 else "red"
            )

            self.levelHitValue.config(
                text="YES" if regs[REG_CONTACT] == 1 else "NO",
                fg="green" if regs[REG_CONTACT] == 1 else "red"
            )

            self.motorStatusValue.config(
                text="ON" if regs[REG_MOTOR] == 1 else "OFF",
                fg="green" if regs[REG_MOTOR] == 1 else "red"
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
                    fg="green" if regs[REG_THROUGHPUT] < 10 else "red")
            self.throughputSlider.set(regs[REG_THROUGHPUT])

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
