class Buzzer:
    ON = "1"
    OFF = "0"

    def __init__(self):
        self.path = "/dev/buzzer"

    def set_to(self, status):
        if status == Buzzer.ON:
            return self.set_on()
        elif status == Buzzer.OFF:
            return self.set_off()
        else:
            return False

    def set_on(self):
        try:
            with open(self.path, 'w') as f:
                f.write(Buzzer.ON)
                return True
        except PermissionError as e:
            return "[PermissionError]: Buzzer device cannot be found or cannot be operated."
        except FileNotFoundError as e:
            return "[FileNotFoundError]: Buzzer device cannot be found on this machine."

    def set_off(self):
        try:
            with open(self.path, 'w') as f:
                f.write(Buzzer.OFF)
                return True
        except PermissionError as e:
            return "[PermissionError]: Buzzer device cannot be found or cannot be operated."
        except FileNotFoundError as e:
            return "[FileNotFoundError]: Buzzer device cannot be found on this machine."


