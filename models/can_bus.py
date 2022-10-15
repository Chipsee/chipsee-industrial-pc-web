import can
import subprocess
from lib.chipsee_board import board

class CanBus(object):
    def __init__(self):
        self.can_dev_path = board.devices().get("can")
        if not self.can_dev_path:
            self.bus = None
            print("Cannot find CAN settings in board config. CAN bus not initialized.")
            return
        self.bring_up_can_device()
        try:
            self.bus = can.Bus(
                interface = 'socketcan',
                channel = self.can_dev_path,
                bitrate = 500000,
                receive_own_messages = False
            )
        except OSError as e:
            self.bus = None
            print("CAN bus not initialized. CAN bus initialization error: {}".format(e))
        
    def bring_up_can_device(self):
        """
        If CAN bus device is not brought up from Linux, eg, with the "ip link up..." command,
        CAN device will not work.
        This method calls the Linux command for you to bring the CAN device up, if you do not
        need CAN device, or your Linux user doesn't have sudo privilege, please comment out the method call.
        """
        can_init_cmd = ['sudo', 'ip', 'link', 'set', self.can_dev_path, 'type', 'can', 'bitrate', '50000', 'triple-sampling', 'on']
        can_up_cmd = ['sudo', 'ip', 'link', 'set', self.can_dev_path, 'up']
        subprocess.run(can_init_cmd)
        max_attempts = 3
        # Sometimes CAN device responds with a `RTNETLINK answers: No such device` error.
        # Retry can resolve the error and bring CAN up. (Noticed on PX30)
        for i in range(max_attempts):
            return_code = subprocess.run(can_up_cmd).returncode
            if return_code == 0:
                break # OK, can is brought up successfully.
            elif return_code == 2:
                continue
        
    def send(self, payload):
        if self.bus is None:
            return
        id = payload.get("id")
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
            print("CAN bus can.exceptions.CanOperationError: {}. Did you bring up the CAN interface of this device?".format(e))

    def start_recv(self, emit_to):
        try:
            for msg in self.bus:
                emit_to.emit('can_recv', { 'data': str(msg) })
        except can.exceptions.CanOperationError as e:
            print("CAN BUS OSError {}. Did you bring up the CAN interface of this device?".format(e))