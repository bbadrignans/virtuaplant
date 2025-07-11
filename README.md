# VirtuaPlant

VirtuaPlant is a Industrial Control Systems simulator which adds a “similar to real-world control logic” to the basic “read/write registers” feature of most PLC simulators. Paired with a game library and 2d physics engine, VirtuaPlant is able to present a GUI simulating the “world view” behind the control system allowing the user to have a vision of the would-be actions behind the control systems.

All the software is written in Python. The idea is for VirtuaPlant to be a collection of different plant types using different protocols in order to be a learning platform and testbed.

The first release introduces a as-simple-as-it-can-get one-process “bottle-filling factory” running Modbus as its protocol.

## Components
### World View

World View consits on the game and 2d physics engine, simulating the effects of the control systems’ action on virtual (cyberz!) assets.

It uses python’s pygame and pymunk (Chipmunk engine for python).

### PLC controller

The soft-plc is implemented over the pymodbus library which runs on a separate thread in the World View component and shares its context (i.e. Registers/Inputs) with the World View functions in order to simulate assets being “plugged in” to the controller.

### HMI

The HMI is written using GTK3 and is quite dead simple. Also runs pymodbus client on a separate thread and connects over TCP/IP to the server (so it could be technically on a separate machine), constantly polling (i.e. reading) the server’s (soft PLC in World View) registers. Control is also possible by writing in the soft-PLC registers.

### Attack scripts

You didn’t thought I was leaving this behind, did you? The phun on having a World View is to see the results when you start messing around with the soft-PLCs registers! Some pre-built scripts for determined actions are available so you can unleash the script-kiddie on yourself and make the plant go nuts! YAY!

## Installation requirements

The following packages are required:

* PyGame
* PyMunk
* PyModbus (requires pycrypto, pyasn1)
* PyGObject / GTK

On debian-based systems (like Ubuntu) you can apt the packages which are not provided over pip:

    apt install python3 pip python3-tk

Then install the pip ones:

    pip install < requirements.txt

## Running

Enter the `/plants` directory, select the plant you want (currently only one available) and start both the world simulator and the HMI with the `start.sh` script. Parts can be ran individually by running `world.py` and `hmi.py` (self-explanatory). All the attack scripts are under the `/attacks` subdirectory.

## Files Explanation

### 📁 **Modbus.py**

The `modbus.py` file allows to create **Modbus TCP servers and clients**. The client part inherited from `ModbusTcpClient` and allows you to **read and write registers**. It includes **connection exception management**, which is important to ensure reliable communication.  
For example, if reading fails, the client tries to **reconnect** before trying to read again.

On the server side, the `modbus.py` library is used to create a **Modbus TCP server** with a **simulated memory block**, which is suitable for testing or prototyping.  
The **identity of the server** is defined with information such as the **product name** and the **supplier**. The server indefinitely waits for connections.

---

### 📁 **world.py**

The file `world.py` implements a **visual and physical simulation** of a **bottle filling plant**.  
This simulation uses the `pygame` library for **graphic display** and `pymunk` for **physics management** (collisions, object movement).

The program creates one **Modbus TCP server**, simulating a **PLC**.  
These servers use the `ServerModbus` class defined in `modbus.py`, which enables **Modbus registers** to be accessible from the network (for hmi.py and attack scripts).  

The simulation follows several **states** that reflect the state of the components.  
For example:
- The **motor** advances the bottles along a line,
- The **nozzle** fills the bottles,
- The **sensors** detect the presence or absence of bottles.

**Physical objects** such as **bottles**, **balls**, **floors**, and **nozzles** are created in `pymunk`'s physical space with properties such as **mass**, **friction**, and **collision**.

The program uses a thread to run the Modbus servers, so that the simulation can run in **real time** while listening to Modbus requests.

---

### 📁 **hmi.py**

`hmi.py` creates a **graphical window** showing the **real-time status** of the bottle filling process simulated in `world.py`.

It connects to the `world.py` **Modbus server** to read **sensor information** (bottle position, liquid level), and **actuator status** (motor, nozzle).

The HMI updates this information **every second** and displays whether the machine is **running** or **stopped**.

The user can click on **"Run"** or **"Stop"** to start or stop the simulation, which sends a command via **Modbus** to the `world.py` server.

If the **connection is lost**, the interface indicates that it is **offline (N/A)** and attempts to **reconnect automatically**.

> In this way, `hmi.py` serves as a **simple control and visualization interface**, communicating directly with the **physical and logical process simulation** in `world.py` via **Modbus**.

---

### 📁 **Attack files**

These **attack scripts** connect to the **Virtuaplant virtual machine** via **Modbus**.

They **write in specific registers** of the Modbus server simulated by `world.py` to **force the machine into different modes**:
- Never stop
- Stop all
- Stop + fill
- Move + fill
