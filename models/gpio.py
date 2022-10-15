from lib.chipsee_board import board

class GPIO:
    HIGH = 1
    LOW = 0

    def __init__(self):
        """
        Properties:
        - inputs & outputs: dict or None. The mapping from a short name to Linux gpio file path, e.g.:
                { "in_1": "/dev/chipsee-gpio5" }, { "out_2": "/dev/chipsee-gpio2" }
        """
        self.inputs = board.devices().get("gpio_in") or {}
        self.outputs = board.devices().get("gpio_out") or {}

    def output(self, outputX, value):
        if not self.validate_output(outputX, value):
            return False
        try:
            with open(self.outputs[outputX], 'w') as f:
                f.write(str(value))
                return True
        except PermissionError as e:
            return "[PermissionError]: GPIO device {} cannot be found or cannot be operated.".format(outputX)
        except FileNotFoundError as e:
            return "[FileNotFoundError]: GPIO device {} cannot be found on this machine.".format(outputX)

    def input(self, inputX):
        if not self.validate_input(inputX):
            return False
        try:
            with open(self.inputs[inputX], 'r') as f:
                return f.read()
        except FileNotFoundError as e:
            return "[FileNotFoundError]: GPIO device {} cannot be found on this machine.".format(inputX)

    def status(self, gpioX):
        """
        Check current status of GPIO pin, especially for GPIO out.
        """
        if gpioX in self.inputs:
            return self.input(gpioX)
        if gpioX in self.outputs:
            try:
                with open(self.outputs[gpioX], 'r') as f:
                    return f.read()
            except PermissionError as e:
                return "[PermissionError]: GPIO device {} cannot be found or cannot be operated.".format(gpioX)
            except FileNotFoundError as e:
                return "[FileNotFoundError]: GPIO device {} cannot be found on this machine.".format(gpioX)
        return False
            
    def validate_input(self, inputX):
        """
        InputX are, e.g.: /dev/chipsee-gpio5 ~ /dev/chipsee-gpio8 for IN1 ~ IN4 for CM4.
        Invalid request to set GPIO input hardware should be rejected.
        """
        return True if (inputX in self.inputs) else False

    def validate_output(self, outputX, value):
        """
        OutputX are, e.g.: /dev/chipsee-gpio1 ~ /dev/chipsee-gpio4 for OUT1 ~ OUT4 for CM4.
        Invalid request to set GPIO output hardware should be rejected.
        """
        is_valid = (outputX in self.outputs) and (value in [GPIO.HIGH, GPIO.LOW])
        return True if is_valid else False

