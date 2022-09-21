from flask import Flask
from flask import Response, request
import json
import os
from flask import render_template

from lib.brightness import Brightness
from lib.gpio import GPIO

app = Flask(__name__)
cm4_gpio = GPIO()

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/brightness', methods=['POST', 'GET'])
def brightness():
    if request.method == 'POST':
        new_brightness = request.form["brightness"]
        brightness = Brightness()
        brightness.set_brightness(brightness=new_brightness)
        actual_brightness = brightness.get_actual_brightness()
        return render_template('brightness.html', actual_brightness=actual_brightness)
    if request.method == 'GET':
        brightness = Brightness()
        actual_brightness = brightness.get_actual_brightness()
        # actual_brightness = 50
        return render_template('brightness.html', actual_brightness=actual_brightness)
    return render_template('brightness.html')

@app.route("/gpio")
def gpio():
    # in_1 = gpio.input(GPIO.IN1)
    # in_2 = gpio.input(GPIO.IN2)
    # in_3 = gpio.input(GPIO.IN3)
    # in_4 = gpio.input(GPIO.IN4)
    in_1 = "Unknown"
    in_2 = "Unknown"
    in_3 = "Unknown"
    in_4 = "Unknown"
    return render_template('gpio.html', in_1=in_1, in_2=in_2, in_3=in_3, in_4=in_4)

@app.route('/api/brightness', methods=['POST'])
def api_brightness():
    new_brightness = request.form["brightness"]
    brightness = Brightness()
    brightness.set_brightness(brightness=new_brightness)
    actual_brightness = brightness.get_actual_brightness()
    # actual_brightness = new_brightness
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
