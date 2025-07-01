# VirtuaPlant

VirtuaPlant is a Industrial Control Systems simulator which adds a “similar to real-world control logic” to the basic “read/write tags” feature of most PLC simulators. Paired with a game library and 2d physics engine, VirtuaPlant is able to present a GUI simulating the “world view” behind the control system allowing the user to have a vision of the would-be actions behind the control systems.

All the software is written in (guess what?) Python. The idea is for VirtuaPlant to be a collection of different plant types using different protocols in order to be a learning platform and testbed.

The first release introduces a as-simple-as-it-can-get one-process “bottle-filling factory” running Modbus as its protocol.

## Components
### World View

![World View](http://wroot.org/wp/wp-content/uploads/2015/03/worldview.png)

World View consits on the game and 2d physics engine, simulating the effects of the control systems’ action on virtual (cyberz!) assets.

It uses python’s pygame and pymunk (Chipmunk engine for python — intended to be replaced by pybox2d due the lack of swept collision handling which currently limits us a little).

### PLC controller

The soft-plc is implemented over the pymodbus library which runs on a separate thread in the World View component and shares its context (i.e. Registers/Inputs/Tags) with the World View functions in order to simulate assets being “plugged in” to the controller.

### HMI

![HMI](http://wroot.org/wp/wp-content/uploads/2015/03/hmi.png)

The HMI is written using GTK3 and is quite dead simple. Also runs pymodbus client on a separate thread and connects over TCP/IP to the server (so it could be technically on a separate machine), constantly polling (i.e. reading) the server’s (soft PLC in World View) tags. Control is also possible by writing in the soft-PLC tags.

### Attack scripts

![Attack all the things](http://wroot.org/wp/wp-content/uploads/2015/03/spill.png)

You didn’t thought I was leaving this behind, did you? The phun on having a World View is to see the results when you start messing around with the soft-PLCs tags! Some pre-built scripts for determined actions are available so you can unleash the script-kiddie on yourself and make the plant go nuts! YAY!

Check the [demo on YouTube](https://www.youtube.com/watch?v=kAfV8acCwfw)

## Installation requirements

The following packages are required:

* PyGame
* PyMunk
* PyModbus (requires pycrypto, pyasn1)
* PyGObject / GTK

On debian-based systems (like Ubuntu) you can apt-get the packages which are not provided over pip:

    apt-get install python-pygame python-gobject python-pip python-dev libcairo2-dev

Then install the pip ones:

    pip install pymunk
    pip install pymodbus
    pip install pyasn1
    pip install pycrypto

or install all of the pip packages by using our provided requirement.txt file:

    pip install < requirements.txt


## Running

Enter the `/plants` directory, select the plant you want (currently only one available) and start both the world simulator and the HMI with the `start.sh` script. Parts can be ran individually by running `world.py` and `hmi.py` (self-explanatory). All the attack scripts are under the `/attacks` subdirectory.

## Files Explanation

### 📁 **Modbus.py**

The `modbus.py` file creates a **Modbus TCP server and client**. The client part inherited from `ModbusTcpClient` and allows you to **read and write registers**. It includes **connection exception management**, which is important to ensure reliable communication.  
For example, if reading fails, the client tries to **reconnect** before trying to read again.

On the server side, the `modbus.py` library is used to create a **Modbus TCP server** with a **simulated memory block**, which is suitable for testing or prototyping.  
The **identity of the server** is defined with information such as the **product name** and the **supplier**, which is used in real context. The server starts with a **blocking function**, which means that the script indefinitely waits for connections.

---

### 📁 **world.py**

The file `world.py` implements a **visual and physical simulation** of a **bottle filling plant**.  
This simulation uses the `pygame` library for **graphic display** and `pygame` for **physics management** (collisions, object movement).

The program creates several **Modbus TCP servers**, each simulating a **PLC** or a component such as a **motor**, **nozzle**, **level sensor** or **contact sensor**.  
These servers use the `ServerModbus` class defined in `modbus.py`, which enables **Modbus registers** to be managed for each component.  
In addition, **Modbus clients** (`ClientModbus`) are instantiated to **read and write values** to these servers, creating interaction between physical simulation and Modbus data.

The simulation follows several **states** that reflect the state of the components.  
For example:
- The **motor** advances the bottles along a line,
- The **nozzle** fills the bottles,
- The **sensors** detect the presence or absence of bottles.

These states are **read or written** via Modbus clients, which communicate with internal Modbus servers, **mimicking a real industrial system** with data exchange via Modbus TCP.

**Physical objects** such as **bottles**, **balls**, **floors**, and **nozzles** are created in `pymunk`'s physical space with properties such as **mass**, **friction**, and **collision**.

The program uses **multiple threads** to run the Modbus servers in parallel, so that the simulation can run in **real time** while listening to Modbus requests.

> The combination of **Modbus** and **physical simulation** illustrates how a **PLC and its sensors/motors** can be modeled and tested in a **virtual environment**.

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

These **attack scripts** are small **advanced control tools** that connect to the **Virtuaplant virtual machine** via **Modbus**.

They **write in specific registers** of the Modbus server simulated by `world.py` to **force the machine into different modes**:
- Never stop
- Stop all
- Stop + fill
- Move + fill

While they maintain these modes, they **wait for the user to press Enter** to return to the normal state.

These tools show how, using **Modbus**, you can both:
- **Supervise** (via `hmi.py`)
- Directly **control or manipulate** the simulated process (via these “attack” scripts)

> This illustrates the **power** and **potential risks** of **industrial protocols** such as **Modbus**, where **simple commands** can **modify machine behavior**.


## Future
### The following plant scenarios are being considered:

* Oil Refinery Boiler
* Nuclear Power Plant Reactor
* Steel Plant Furnace

### The following protocols are being considered:
* DNP3 (based on OpenDNP3)
* S7
