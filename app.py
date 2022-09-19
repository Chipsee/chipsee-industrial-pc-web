from flask import Flask
from flask import Response, request
import json
import os


app = Flask(__name__)

@app.route("/")
def home():
    return "<p>OK</p>"
