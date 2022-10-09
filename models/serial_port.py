import serial
from lib.chipsee_board import board

class SerialPort(object):
    """
    RS232 and RS485 can share this same class.
    params:
    - name: The name of serial device assigned in `config/peripherals/{board_name}` file.
            Each Chipsee board may have one or more serial ports, this class
            uses this name to detect the corresponding Linux Serial device file path.
    """
    def __init__(self, name):
        self.device = board.devices().get(name)
        if self.device is None:
            return
        self.baud_rate = 115200
        self.ser = serial.Serial(self.device, self.baud_rate, timeout=1)

    def tx(self, str_data):
        if self.device is None:
            return
        data = f"{str_data}\n".encode("utf-8")
        self.ser.write(data)

    def rx(self):
        if self.device is None:
            return
        data = self.ser.readline().decode("utf-8")
        return data
