from lib.chipsee_board import board

class Buzzer(object):
    ON = "1"
    OFF = "0"

    def __init__(self):
        self.device = board.devices().get("buzzer")
        if self.device is None:
            print("Buzzer: cannot find buzzer device in config file, buzzer not initialized.")

    def set_to(self, status):
        if self.device is None:
            return False

        if status == Buzzer.ON:
            return self.set_on()
        elif status == Buzzer.OFF:
            return self.set_off()
        else:
            return False

    def set_on(self):
        if self.device is None:
            return

        try:
            with open(self.device, 'w') as f:
                f.write(Buzzer.ON)
                return True
        except PermissionError as e:
            return "[PermissionError]: Buzzer device cannot be found or cannot be operated."
        except FileNotFoundError as e:
            return "[FileNotFoundError]: Buzzer device cannot be found on this machine."

    def set_off(self):
        if self.device is None:
            return

        try:
            with open(self.device, 'w') as f:
                f.write(Buzzer.OFF)
                return True
        except PermissionError as e:
            return "[PermissionError]: Buzzer device cannot be found or cannot be operated."
        except FileNotFoundError as e:
            return "[FileNotFoundError]: Buzzer device cannot be found on this machine."


