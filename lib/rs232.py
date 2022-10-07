import serial

class RS232(object):
    def __init__(self):
        # self.device = "/dev/cu.usbserial-1420"
        # self.device = "/dev/ttyAMA1" # For CM4 7inch, CS10600RA4070 RS232-2
        self.device = "/dev/ttyS3" # For All in One, CS12800PX101A
        self.baud_rate = 115200
        self.ser = serial.Serial(self.device, self.baud_rate, timeout=1)

    def tx(self, str_data):
        data = f"{str_data}\n".encode("utf-8")
        self.ser.write(data)

    def rx(self):
        data = self.ser.readline().decode("utf-8")
        return data
