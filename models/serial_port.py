import serial
from lib.chipsee_board import board
import time
                
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
            print("{}: cannot find serial device in config file, serial device not initialized.".format(name))
            return
        self.baud_rate = 115200
        self.ser = serial.Serial(self.device, self.baud_rate, timeout=10)
        self.ser.close()
        self.closed = True
        self.reader = ReadLine(self.ser)

    def open(self):
        self.ser.open()
        self.closed = False
        
    def close(self):
        self.ser.close()
        self.closed = True
        
    def tx(self, str_data):
        if self.device is None:
            return
        if self.closed:
            return
        data = f"{str_data.strip()}\n".encode("utf-8")
        self.ser.write(data)

    def rx(self):
        if self.device is None:
            return None

        while(True):
            if self.closed:
                time.sleep(1)
                return 0
            try:
                data = self.reader.readline()
                if data:
                    return data.decode("utf-8")
                else:
                    # Serial Port closed.
                    return 0
            except serial.serialutil.SerialException as e:
                print(e)
                continue



class ReadLine:
    """
    A helper class that does nothing but speeds up reading through pyserial
    Reference: https://github.com/pyserial/pyserial/issues/216
    """
    def __init__(self, ser):
        self.buf = bytearray()
        self.ser = ser
    
    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            try:
                i = max(1, min(2048, self.ser.in_waiting))
                data = self.ser.read(i)
                i = data.find(b"\n")
                if i >= 0:
                    r = self.buf + data[:i+1]
                    self.buf[0:] = data[i+1:]
                    return r
                else:
                    self.buf.extend(data)
            except TypeError:
                # Serial Port closed before readline is returned.
                return None