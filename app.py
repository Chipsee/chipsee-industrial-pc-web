import gevent  # (Websocket support)
from gevent import monkey  # (Websocket support)
monkey.patch_all()  # (Websocket support) This patch should be carried out as early as possible.

from flask import Flask, redirect, render_template
from flask import request
from flask import send_from_directory # (Download file support)
from flask_socketio import SocketIO, emit # (Websocket support)

UPLOAD_FOLDER = 'storage/' # (Download file support)
from lib.server_control import ServerControl

from models.brightness import Brightness
from models.gpio import GPIO
from models.serial_port import SerialPort
from models.buzzer import Buzzer
from models.can_bus import CanBus
from models.ip_config import IpConfig
from models.file_upload import FileUpload
from models.modbus_server_sync import ModbusServerSync
from models.modbus_client_sync import ModbusClientSync

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # (Download file support)
socketio = SocketIO(app, async_mode="gevent")

dev_gpio = GPIO()
dev_rs232 = SerialPort(name="rs232")
dev_rs485 = SerialPort(name="rs485")
dev_brightness = Brightness()
dev_buzzer = Buzzer()
dev_can_bus = CanBus()
dev_modbus_servers = {
    "tcp": ModbusServerSync(comm="tcp", emit_to=socketio),
    "serial": ModbusServerSync(comm="serial", emit_to=socketio, serial_device_name="rs485")
}
dev_modbus_clients = {
    "tcp": ModbusClientSync(comm="tcp", emit_to=socketio),
    "serial": ModbusClientSync(comm="serial", emit_to=socketio, serial_device_name="rs485")
}

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/cases")
def cases():
    return render_template('cases.html')

@app.route("/diagrams")
def diagrams():
    return render_template('diagrams.html')

# Brightness
@app.route('/brightness', methods=['GET', 'POST'])
def brightness():
    if request.method == 'GET':
        actual_b = dev_brightness.get_actual_brightness()
        max_b = dev_brightness.max_brightness or "100"
        return render_template('brightness.html', actual_brightness=actual_b, max_brightness=max_b)
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

# Serial RS232
@app.route("/rs232")
def rs232():
    return render_template('rs232.html', closed=dev_rs232.closed)

@app.route("/api/rs232", methods=['POST'])
def api_rs232():
    # Open / Close Serial Port on POST form.
    req = request.json
    new_status = str(req['status'])
    if new_status == "1":
        dev_rs232.open()
    elif new_status == "0":
        dev_rs232.close()
    return { 'status': 'Success', 'msg': new_status }

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

# Serial RS485
@app.route("/rs485")
def rs485():
    return render_template('rs485.html', closed=dev_rs485.closed)

@app.route("/api/rs485", methods=['POST'])
def api_rs485():
    # Open / Close Serial Port on POST form.
    req = request.json
    new_status = str(req['status'])
    if new_status == "1":
        dev_rs485.open()
    elif new_status == "0":
        dev_rs485.close()
    return { 'status': 'Success', 'msg': new_status }

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

# Modbus Server
@app.route("/modbus_server")
def modbus_server():
    return render_template('modbus_server.html', 
        serial_closed=dev_modbus_servers["serial"].closed, 
        tcp_closed=dev_modbus_servers["tcp"].closed
    )

@app.route("/api/modbus_server", methods=['POST'])
def api_modbus_server():
    # Start / stop Modbus server on POST form.
    req = request.json
    new_status = str(req['status'])
    comm = str(req['comm'])
    if new_status == "1":
        thread = gevent.spawn(run_modbus(comm))
        # Modbus server will block running from here, until stopped.
        thread.kill()
        return { 'status': 'Success', 'comm': comm, 'msg': 'Blocking modbus server returned.' }
    elif new_status == "0":
        dev_modbus_servers[comm].stop()
        return { 'status': 'Success', 'comm': comm, 'msg': new_status }

def run_modbus(comm):
    dev_modbus_servers[comm].run_server()
    
# Modbus Client
@app.route("/modbus_client")
def modbus_client():
    return render_template('modbus_client.html')

@app.route("/api/modbus_client", methods=['POST'])
def api_modbus_client():
    req = request.json
    comm = str(req['comm'])
    if comm == "tcp":
        dev_modbus_clients["tcp"].run_client()
    elif comm == "serial":
        dev_modbus_clients["serial"].run_client()
    return { 'status': 'Success', 'data': 'OK' }

# CAN Bus
@app.route("/can_bus")
def can_bus():
    closed = dev_can_bus.closed
    return render_template('can_bus.html', closed=closed)

@socketio.on('can_send')
def can_send(data):
    # Listen to browser CAN form/button instructions, then send the data through CAN hardware.
    dev_can_bus.send(data)

@app.route("/api/can_bus", methods=['POST'])
def api_can_bus():
    # Start / stop CAN bus receiver on POST form.
    req = request.json
    new_status = str(req['status'])
    if new_status == "1":
        gevent.spawn(can_recv) # background task to read CAN device
        return { 'status': 'Success', 'msg': 'CAN started.' }
    elif new_status == "0":
        dev_can_bus.close_receiver()
        return { 'status': 'Success', 'msg': new_status }
    
def can_recv():
    # Listen to CAN hardware in the background, if data comes, push it to the browser.
    dev_can_bus.start_recv(emit_to=socketio)

# Cases: Static IP setting
@app.route('/ip_config', methods=['GET', 'POST'])
def ip_config():
    dev_ip_config = IpConfig()
    if request.method == 'GET':
        return render_template('ip_config.html', nics=dev_ip_config.nics)
    if request.method == 'POST':
        res = dev_ip_config.handle_form(request.form)
        return render_template('ip_config.html', nics=dev_ip_config.nics, msg=res.get("msg"), form_errors=res.get("errors"))

# Cases: Uploading and Downloading File
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

# Cases: Video Play
@app.route("/video_play")
def video_play():
    return render_template('video_play.html')

# Cases: Audio Play
@app.route("/audio_play")
def audio_play():
    return render_template('audio_play.html')

# Diagrams: Charts Showcase
@app.route('/charts')
def charts():
    return render_template('charts.html')

# Diagrams: Line Chart
@app.route('/line_chart')
def line_chart():
    actual_brightness = dev_brightness.get_actual_brightness()
    return render_template('line_chart.html', actual_brightness=actual_brightness)

@app.route('/api/line_chart', methods=['GET', 'POST'])
def api_line_chart():
    if request.method == 'GET':
        actual_brightness = dev_brightness.get_actual_brightness()
        return {"brightness": actual_brightness}
    if request.method == 'POST':
        new_brightness = request.form["brightness"]
        dev_brightness.set_brightness(brightness=new_brightness)
        actual_brightness = dev_brightness.get_actual_brightness()
        return {"brightness": actual_brightness}
    
# Diagrams: Sine Wave
@app.route('/sine_wave')
def sine_wave():
    return render_template('sine_wave.html')

# Diagrams: Bar Chart
@app.route('/bar_chart')
def bar_chart():
    return render_template('bar_chart.html')

# Diagrams: Doughnut Chart
@app.route('/doughnut_chart')
def doughnut_chart():
    return render_template('doughnut_chart.html')

# Common: Server Controls
@app.route('/api/server_control', methods=['POST'])
def server_control():
    cmd = str(request.json['cmd'])
    ServerControl().run(cmd)
    return  { 'status': 'Success', 'msg': 'OK' }
    
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
