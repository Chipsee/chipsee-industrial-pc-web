# Web GUI Demo (HMI) for Chipsee Industrial PCs

## Supported Hardware
1. Chipsee Cortex®-A72 Raspberry Pi® series [EPC/PPC-CM4-70 (PN: CS10600RA4070)](https://docs.chipsee.com/PCs/Pi/A72/Manuals/Hardware/CS10600RA4070.html#epc-ppc-cm4-70) Industrial Pi PC
1. Chipsee [AIO-PX30-101 (PN: CS12800PX101A)](https://docs.chipsee.com/PCs/ARM/PX30/AIO/Manuals/Hardware/CS12800PX101A.html) Industrial PC 
## Operating System

Debian 10 that comes with Chipsee Industrial PC, with pre-installed hardware peripheral drivers.

## Software

Programming language: **Python3** in the web server, **Javascript** in the web browser

Web framework: **Flask**

Browser: **Chromium**

## Introduction
This demo is a Python-Flask web application for testing the GPIO, buzzer, serial ports(RS232 and RS485) and screen panel's brightness of Chipsee Industrial PC.

It contains 6 HTML web pages to control input and output of these peripherals, 
4 Python classes to control the logic of these peripherals,
a Flask web server to handle the HTTP requests for us.

## How to Install
Use a Linux user with `sudo` privilige, e.g. on CM4 just use pi, on PX30 you can use root (`sudo su` to switch to root user. Or create a user with sudo privilege), otherwise some hardware may or may not work, such as screen brightness.

```bash
git clone https://github.com/printfinn/cm4_demo_python_flask.git
cd cm4_demo_python_flask
# Create a Python project virtual environment
python3 -m venv venv
# Activate the virtual environment
. venv/bin/activate
# Upgrade Pip if your pip version is too old (< 21.0)
pip install --upgrade pip
# Install the required Python packages
pip install -r requirements.txt
# Alternatively, upgrade setuptools (this will install dependency for gunicorn, recommended to execute)
pip install -U setuptools
```

## How to start
```bash
# Re-activate the virtual environment if you have exited from it
. venv/bin/activate
# Start the demo using Flask for development (handy for debugging, but not recommended. This has a bad performance for websocket server, may cause serial device to lose data in some situations.)
python app.py
# or, start the demo for production (also recommended for development)
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 app:app
```
Then go to Chromium web browser and enter address `127.0.0.1:5000` in the address bar of web browser.

## How to stop
Press ctrl + C to stop the Flask web server, then exit the virtual environment with:
```bash
deactivate
```
## Code Structure
### app.py
`app.py` is the entry file of a Flask web app.

### models folder
`models` folder contains the logic code to control different peripherals, for example: `models/brightness.py` contains code that adjusts the brightness of a PC's screen, `models/serial_port.py` contains code to utilize the RS232 and RS485 serial ports.

### templates folder
`templates` folder is the Flask's convention of storing html web pages. In this app, each peripheral has a html file in the templates folder. For example: `templates/brightness.html` is an example web page of how user could use a browser as GUI to adjust the brightness of a PC's screen.

### static folder
`static` folder contains the CSS, images and some JS files.

### config folder
`config` folder contains the configurations of this app. It has a `peripherals` sub directory, which contains PC-specific settings for different Chipsee PCs, for example: `config/peripherals/CS10600RA4070.json` file contains the `Chipsee Industrial Pi`'s peripherals' Linux file paths, `config/peripherails/CS12800PX101A.json` file contains the file path of the `PX30` PC. Those file path may or may not differ between different PCs, this is a convenient way to organize the configuration of different PCs. You can also hard-code the Linux file path in each model's Python classes (inside `models/{peripheral_name}.py` if your code are not designed to support different PCs.

## Notes for Developers
1. This demo uses Flask because Python code is easier to understand and Flask is a simpler Python web server.
You can indeed use any web framework you wish: Nodejs, Ruby on Rails, Django, Phoenix, Laravel etc, or some other C++, Java web frameworks. The Chipsee Industrial PC is powerful enough to run any of these.
1. If you're using another web framework that is not written in Python, we encourage you to read the code in `models` folder of this repo, and
read the [Chipsee software documents](https://docs.chipsee.com/PCs/Pi/Software/Debian.html) to figure out how to manipulate the hardware
peripherals of Chipsee Industrial PC in your chosen programming language. We'll provide more examples for different programming languages
in the future, but any experienced programmer should be able to figure it out by themselves. Here are some hints:
    1. **GPIO**: GPIO are files on the Linux OS, manipulate them by reading writing these files: `/dev/chipsee-gpio1` ~ `/dev/chipsee-gpio8`
    1. **Screen Panel Brightness**: Brightness can be interacted with a bunch of Linux files in: `/sys/class/backlight/pwm-backlight`
    1. **Serial Port**: Use a Serial library to talk to Linux serial device. Python has `pyserial`, Ruby has a ruby-serialport [gem](https://github.com/hparra/ruby-serialport), JS has node-serialport [library](https://github.com/serialport/node-serialport), C++, Java should have their own solutions. Since Chipsee's Industrial Pi's RS232 serial port is just a Linux serial device, you can use any libraries that can handle Linux serial devices to control it.
    1. **Buzzer**: Control a buzzer with writing to Linux file: `/dev/buzzer`.
    1. **CAN Bus**: CAN devices are abstracted as Linux network interfaces in the Linux kernel, use `ifconfig` to check them, use `ip link set can0 ***` commands to configure and enable them. Then use a CAN library to send / receive messages through CAN hardware, like `python-can`. We haven't tested other languages, but other programming languages should have their own solutions to control a CAN device.
1. In the browser client, you can use FETCH API or XHR to visit your web server's API endpoint, to send control signals to the hardware peripherals, so that you don't need to refresh the page. But if you want to test with a traditional request-response cycle, it's also fine.
1. You can also use a WebSocket for continously reading status of GPIO/Serail Port. This demo uses `poll` strategy for reading GPIO input status, and uses `websocket` to read serial ports and CAN messages. They're not mandatory, pick the solution that works best for your problem!

