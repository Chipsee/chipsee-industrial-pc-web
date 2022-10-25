import gevent  # (Websocket support)
from gevent import monkey  # (Websocket support)
monkey.patch_all()  # (Websocket support) This patch should be carried out as early as possible.

from flask import Flask, redirect, render_template
from flask import request
from flask import send_from_directory # (Download file support)
from flask_socketio import SocketIO, emit # (Websocket support)

UPLOAD_FOLDER = 'storage/' # (Download file support)

from models.brightness import Brightness
from models.gpio import GPIO
from models.serial_port import SerialPort
from models.buzzer import Buzzer
from models.can_bus import CanBus
from models.ip_config import IpConfig
from models.file_upload import FileUpload

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # (Download file support)
socketio = SocketIO(app, async_mode="gevent")

dev_gpio = GPIO()
dev_rs232 = SerialPort(name="rs232")
dev_rs485 = SerialPort(name="rs485")
dev_brightness = Brightness()
dev_buzzer = Buzzer()
dev_can_bus = CanBus()

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/cases")
def cases():
    return render_template('cases.html')

# Brightness
@app.route('/brightness', methods=['GET', 'POST'])
def brightness():
    if request.method == 'GET':
        actual_brightness = dev_brightness.get_actual_brightness()
        return render_template('brightness.html', actual_brightness=actual_brightness)
    if request.method == 'POST':
        new_brightness = request.form["brightness"]
        dev_brightness.set_brightness(brightness=new_brightness)
        actual_brightness = dev_brightness.get_actual_brightness()
        return render_template('brightness.html', actual_brightness=actual_brightness)

@app.route('/api/brightness', methods=['POST'])
def api_brightness():
    new_brightness = request.form["brightness"]
    dev_brightness.set_brightness(brightness=new_brightness)
    actual_brightness = dev_brightness.get_actual_brightness()
    return {"brightness": actual_brightness}

# GPIO
@app.route("/gpio")
def gpio():
    gpio_ins = dev_gpio.inputs
    gpio_outs = dev_gpio.outputs
    return render_template('gpio.html', gpio_ins=gpio_ins, gpio_outs=gpio_outs)

@app.route('/api/gpio/<gpioX>', methods=['GET', 'POST'])
def api_gpio(gpioX):
    if request.method == 'GET':
        msg = dev_gpio.input(inputX=gpioX)
        if msg:
            return { gpioX: msg }
        return { gpioX: "Not a valid Chipsee CM4 GPIO port." }

    if request.method == 'POST':
        req = request.json
        v_out = int(req['v_out'])
        msg = dev_gpio.output(outputX=gpioX, value=v_out)
        if msg == True:
            return { 'status': 'Success', 'msg': gpioX }
        return { 'status': 'Error', 'msg': msg }

@app.route('/api/gpio/<gpioX>/status', methods=['GET'])
def api_gpio_status(gpioX):
    msg = dev_gpio.status(gpioX=gpioX)
    if msg:
        return { gpioX: msg }
    return { gpioX: "Not a valid Chipsee CM4 GPIO port." }
    
# Buzzer
@app.route("/buzzer")
def buzzer():
    return render_template('buzzer.html')

@app.route('/api/buzzer', methods=['POST'])
def api_buzzer():
    req = request.json
    new_status = str(req['buzzer'])
    msg = dev_buzzer.set_to(new_status)
    if msg == True:
        return { 'status': 'Success', 'msg': new_status }
    return { 'status': 'Error', 'msg': msg }

# Serial
@app.route("/rs232")
def rs232():
    return render_template('rs232.html')

@socketio.on('rs232_tx')
def rs232_tx(data):
    # Listen to browser Serial instructions, then send the data through serial hardware.
    dev_rs232.tx(data.get('data'))

def rs232_rx():
    # Continuously read data from Serial Port hardware, if data comes, push it to browser.
    while True:
        data = dev_rs232.rx()
        if data:
            socketio.emit('rs232_rx', { 'data': data })
        if data is None:
            break
gevent.spawn(rs232_rx) # background task to read 232 device

@app.route("/rs485")
def rs485():
    return render_template('rs485.html')

@socketio.on('rs485_tx')
def rs485_tx(data):
    # Listen to browser Serial instructions, then send the data through serial hardware.
    dev_rs485.tx(data.get('data'))

def rs485_rx():
    # Continuously read data from Serial Port hardware, if data comes, push it to browser.
    while True:
        data = dev_rs485.rx()
        if data:
            socketio.emit('rs485_rx', { 'data': data })
        if data is None:
            break
gevent.spawn(rs485_rx) # background task to read 485 device

# CAN Bus
@app.route("/can_bus")
def can_bus():
    return render_template('can_bus.html')

@socketio.on('can_send')
def can_send(data):
    # Listen to browser CAN form/button instructions, then send the data through CAN hardware.
    if not dev_can_bus.bus:
        return
    dev_can_bus.send(data)

def can_recv():
    # Listen to CAN hardware in the background, if data comes, push it to the browser.
    if dev_can_bus.bus is None:
        return
    dev_can_bus.start_recv(emit_to=socketio)
gevent.spawn(can_recv) # background task to read CAN device


# Cases: Line Chart
@app.route('/line_chart')
def line_chart():
    actual_brightness = dev_brightness.get_actual_brightness()
    return render_template('line_chart.html', actual_brightness=actual_brightness)

@app.route('/api/line_chart', methods=['GET', 'POST'])
def api_line_chart():
    if request.method == 'GET':
        # GET request shows an example to provide realtime data to browser from other devices, 
        # but isn't actually used in this line chart html template.
        actual_brightness = dev_brightness.get_actual_brightness()
        return {"brightness": actual_brightness}
    if request.method == 'POST':
        new_brightness = request.form["brightness"]
        dev_brightness.set_brightness(brightness=new_brightness)
        actual_brightness = dev_brightness.get_actual_brightness()
        return {"brightness": actual_brightness}

# Cases: Static IP setting
@app.route('/ip_config', methods=['GET', 'POST'])
def ip_config():
    dev_ip_config = IpConfig()
    if request.method == 'GET':
        return render_template('ip_config.html', nics=dev_ip_config.nics)
    if request.method == 'POST':
        res = dev_ip_config.handle_form(request.form)
        return render_template('ip_config.html', nics=dev_ip_config.nics, msg=res.get("msg"), form_errors=res.get("errors"))

@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():
    if request.method == 'POST':
        fu = FileUpload(folder=app.config["UPLOAD_FOLDER"], request=request)
        res = fu.handle_file_request()
        print(res.get("error"))
        return render_template('file_upload.html', msg=res.get("msg"), error=res.get("error"))
    if request.method == 'GET':
        return render_template('file_upload.html')

@app.route('/uploads/<fname>')
def download_file(fname):
    return send_from_directory(app.config["UPLOAD_FOLDER"], fname, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
