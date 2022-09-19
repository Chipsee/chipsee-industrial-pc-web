from flask import Flask
from flask import Response, request
import json
import os
from flask import render_template

from lib.brightness import Brightness

app = Flask(__name__)

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
