import can
from lib.chipsee_board import board

class CanBus(object):
    def __init__(self):
        try:
            self.bus = can.Bus(
                interface = 'socketcan',
                channel = board.devices().get("can"),
                bitrate = 500000,
                receive_own_messages = False
            )
        except OSError as e:
            self.bus = None
            print("CAN bus not initialized! CAN bus initialization error: {}".format(e))

    def send(self, payload):
        if self.bus is None:
            return
        id = payload.get("id"),
        data = payload.get("data")
        try:
            id = int(id)
        except ValueError as e:
            print("CAN ID error: {}".format(e))
            id = 0
        data = data.replace(".", "")
        encoded_data = data.encode('utf-8')
        byte_array = bytearray(encoded_data)
        message = can.Message(
            arbitration_id = int(id), 
            data = byte_array
        )
        try:
            self.bus.send(message, timeout=0.2)
        except can.exceptions.CanOperationError as e:
            print("CAN error: {}".format(e))


