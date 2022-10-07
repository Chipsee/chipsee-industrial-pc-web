from flask import Flask, render_template
from flask import request

from lib.brightness import Brightness
from lib.gpio import GPIO
from lib.rs232 import RS232
from lib.rs485 import RS485
from lib.buzzer import Buzzer

from flask_sock import Sock
import time

app = Flask(__name__)
sock = Sock(app)
cm4_gpio = GPIO()
cm4_rs232 = RS232()
cm4_rs485 = RS485()
cm4_brightness = Brightness()
cm4_buzzer = Buzzer()

@app.route("/")
def home():
    return render_template('home.html')

@sock.route('/rs232_tx')
def rs232_tx(ws):
    time.sleep(1)
    while True:
        data = ws.receive()
        cm4_rs232.tx(data)
        ws.send(data)

@sock.route('/rs232_rx')
def rs232_rx(ws):
    time.sleep(1)
    while True:
        data = cm4_rs232.rx()
        if data:
            ws.send(data)
        else:
            continue

@sock.route('/rs485_tx')
def rs485_tx(ws):
    time.sleep(1)
    while True:
        data = ws.receive()
        cm4_rs485.tx(data)
        ws.send(data)

@sock.route('/rs485_rx')
def rs485_rx(ws):
    time.sleep(1)
    while True:
        data = cm4_rs485.rx()
        if data:
            ws.send(data)
        else:
            continue

@app.route('/brightness', methods=['POST', 'GET'])
def brightness():
    if request.method == 'POST':
        new_brightness = request.form["brightness"]
        cm4_brightness.set_brightness(brightness=new_brightness)
        actual_brightness = cm4_brightness.get_actual_brightness()
        return render_template('brightness.html', actual_brightness=actual_brightness)
    if request.method == 'GET':
        actual_brightness = cm4_brightness.get_actual_brightness()
        return render_template('brightness.html', actual_brightness=actual_brightness)

@app.route("/gpio")
def gpio():
    in_1 = "Unknown"
    in_2 = "Unknown"
    in_3 = "Unknown"
    in_4 = "Unknown"
    return render_template('gpio.html', in_1=in_1, in_2=in_2, in_3=in_3, in_4=in_4)

@app.route("/rs232")
def rs232():
    return render_template('rs232.html')

@app.route("/rs485")
def rs485():
    return render_template('rs485.html')

@app.route("/buzzer")
def buzzer():
    return render_template('buzzer.html')

@app.route('/api/brightness', methods=['POST'])
def api_brightness():
    new_brightness = request.form["brightness"]
    cm4_brightness.set_brightness(brightness=new_brightness)
    actual_brightness = cm4_brightness.get_actual_brightness()
    return {"brightness": actual_brightness}

@app.route('/api/gpio/<gpioX>', methods=['GET', 'POST'])
def api_gpio(gpioX):
    if request.method == 'GET':
        # return { gpioX: "HIGH" }
        msg = cm4_gpio.input(inputX=gpioX)
        if msg:
            return { gpioX: msg }
        return { gpioX: "Not a valid Chipsee CM4 GPIO port." }

    if request.method == 'POST':
        req = request.json
        v_out = int(req['v_out'])
        # return { gpioX: v_out }
        msg = cm4_gpio.output(outputX=gpioX, value=v_out)
        if msg == True:
            return { 'status': 'Success', 'msg': gpioX }
        return { 'status': 'Error', 'msg': msg }

@app.route('/api/buzzer', methods=['POST'])
def api_buzzer():
    req = request.json
    new_status = str(req['buzzer'])
    # return { 'status': 'Success', 'msg': new_status }
    msg = cm4_buzzer.set_to(new_status)
    if msg == True:
        return { 'status': 'Success', 'msg': new_status }
    return { 'status': 'Error', 'msg': msg }
