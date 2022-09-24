# Web GUI Demo for Chipsee [EPC/PPC-CM4-70](https://docs.chipsee.com/PCs/Pi/A72/Manuals/Hardware/CS10600RA4070.html#epc-ppc-cm4-70) Industrial Pi PC



## Hardware
Chipsee Cortex®-A72 Raspberry Pi® series EPC/PPC-CM4-70 (PN: CS10600RA4070) 

## Operating System

Debian 10 that comes with Chipsee Industrial Pi, with pre-installed hardware peripheral drivers.

## Software

Programming language: **Python3** in the web server, **Javascript** in the web browser

Web framework: **Flask**

Browser: **Chromium**

## Introduction
This demo is a Python-Flask web application for testing the GPIO, Serial Port(RS232) and screen panel's brightness of Chipsee Industrial Pi PC.

It contains 4 HTML web pages to control input and output of these peripherals, 
3 Python classes to control the logic of these peripherals,
a Flask web server to handle the HTTP requests for us.

## How to Install
```bash
git clone https://github.com/printfinn/cm4_demo_python_flask.git
cd cm4_demo_python_flask
# Create a Python project virtual environment
python3 -m venv venv
# Activate the virtual environment
. venv/bin/activate
# Install the required Python packages
pip install -r requirements.txt
```

## How to start
```bash
# Re-activate the virtual environment if you have exited from it
. venv/bin/activate
# Start the demo using Flask
flask run
```
Then go to Chromium web browser and enter address `127.0.0.1:5000` in the address bar of web browser.

## How to stop
Press ctrl + C to stop the Flask web server, then exit the virtual environment with:
```bash
deactivate
```

## Notes for Developers
1. This demo uses Flask because Python code is easier to understand and Flask is a simpler Python web server.
You can indeed use any web framework you wish: Nodejs, Ruby on Rails, Django, Phoenix, Laravel etc, or some other C++, Java web frameworks. The Chipsee Industrial Pi
is powerful enough to run any of these.
1. If you're using another web framework that is not written in Python, we encourage you to read the code in `lib` folder of this repo, and
read the [Chipsee software documents](https://docs.chipsee.com/PCs/Pi/Software/Debian.html) to figure out how to manipulate the hardware
peripherals of Chipsee Industrial Pi in your chosen programming language. We'll provide more examples for different programming languages
in the future, but any experienced programmer should be able to figure it out by themselves. Here are some hints:
    1. **GPIO**: GPIO are files on the Linux OS, manipulate them by reading writing these files: `/dev/chipsee-gpio1` ~ `/dev/chipsee-gpio8`
    1. **Screen Panel Brightness**: Brightness can be interacted with a bunch of Linux files in: `/sys/class/backlight/pwm-backlight`
    1. **Serial Port**: Use a Serial library to talk to Linux serial device. Python has `pyserial`, Ruby has a ruby-serialport [gem](https://github.com/hparra/ruby-serialport), JS has node-serialport [library](https://github.com/serialport/node-serialport), C++, Java should have their own solutions. Since Chipsee's Industrial Pi's RS232 serial port is just a Linux serial device, you can use any libraries that can handle Linux serial devices to control it.
1. In the browser client, you can use FETCH API or XHR to visit your web server's API endpoint, to send control signals to the hardware peripherals, so that you don't need to refresh the page. But if you want to test with a traditional request-response cycle, it's also fine.
1. You can also use a WebSocket for continously reading status of GPIO/Serail Port. This demo uses `poll` strategy for reading GPIO input status, and uses `websocket` to read RS232 port messages. They're not mandatory, pick the solution that works best for your problem!

