import can
import subprocess
from lib.chipsee_board import board

class CanBus(object):
    def __init__(self):
        self.can_dev_path = board.devices().get("can")
        if not self.can_dev_path:
            self.can_up = False
            print("Cannot find CAN settings in board config. CAN bus not initialized.")
            return
        self.bring_up_can_device()
        self.closed = True
        self.bus = None
            
    def close_receiver(self):
        """
        The loop of receiving messages will stop running because of this closed flag. 
        """
        self.closed = True
                
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
                self.can_up = True
                break # OK, can is brought up successfully.
            elif return_code == 2:
                continue
    
    def message_from(self, payload):
        """
        Rewrite HTML web form to CAN message format.
        """
        id = payload.get("id")
        data = payload.get("data")
        try:
            id = int(id)
        except ValueError as e:
            print("CAN bus ID error: {}".format(e))
            id = 0
        data = data.replace(".", "")
        encoded_data = data.encode('utf-8')
        byte_array = bytearray(encoded_data)
        message = can.Message(
            arbitration_id = int(id), 
            data = byte_array
        )
        return message
    
    def send(self, payload):
        """
        Send(broadcast) CAN bus message to connected CAN devices.
        """
        if not self.can_up:
            print("CAN bus is not available or is down.")
            return
        message = self.message_from(payload)
        try:
            if self.bus:
                # Reuse the receiver bus
                self.bus.send(message, timeout=0.2)
            else:
                with can.Bus(
                    interface = 'socketcan',
                    channel = self.can_dev_path,
                    bitrate = 500000,
                    receive_own_messages = False
                ) as bus:
                    bus.send(message, timeout=0.2)
        except OSError as e:
            print("CAN bus not initialized. CAN bus initialization error: {}".format(e))
        except can.exceptions.CanOperationError as e:
            print("CAN bus can.exceptions.CanOperationError: {}. Did you bring up the CAN interface of this device?".format(e))

    def start_recv(self, emit_to):
        if not self.can_up:
            print("CAN bus is not available or is down.")
            return
        try:
            self.closed = False
            while not self.closed:
                with can.Bus(
                    interface = 'socketcan',
                    channel = self.can_dev_path,
                    bitrate = 500000,
                    receive_own_messages = False
                ) as bus:
                    self.bus = bus
                    msg = bus.recv()
                    if not self.closed:
                        # Multiple threads may change the `closed` flag!
                        # This `if` statement is not necessary,
                        # If can bus was closed in another thread, and `bus.recv()` got message
                        # this `if` ensures it is not emitted to the websocket.
                        emit_to.emit('can_recv', { 'data': str(msg) })
            self.bus = None
        except OSError as e:
            print("CAN bus not initialized. CAN bus initialization error: {}".format(e))
        except can.exceptions.CanOperationError as e:
            print("CAN bus OSError {}. Did you bring up the CAN interface of this device?".format(e))