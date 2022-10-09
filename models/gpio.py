class GPIO:
    HIGH = 1
    LOW = 0

    def __init__(self):
        self.inputs = { 'in_1': 5, 'in_2': 6, 'in_3': 7, 'in_4': 8 }
        self.outputs = { 'out_1': 1, 'out_2': 2, 'out_3': 3, 'out_4': 4 }
        self.init_pins()

    def init_pins(self):
        self.path = "/dev/chipsee-gpio"
        self.gpio_devices = {} # The corresponding Linux device files.
        for key, pin in self.inputs.items():
            self.gpio_devices[key] = self.path + str(pin)
        for key, pin in self.outputs.items():
            self.gpio_devices[key] = self.path + str(pin)

    def output(self, outputX, value):
        if not self.validate_output(outputX, value):
            return False
        try:
            with open(self.gpio_devices[outputX], 'w') as f:
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
            with open(self.gpio_devices[inputX], 'r') as f:
                return f.read()
        except FileNotFoundError as e:
            return "[FileNotFoundError]: GPIO device {} cannot be found on this machine.".format(inputX)

    def validate_input(self, inputX):
        """
        InputX are /dev/chipsee-gpio5 ~ /dev/chipsee-gpio8 for IN1 ~ IN4
        """
        return True if (inputX in self.inputs) else False

    def validate_output(self, outputX, value):
        """
        OutputX are /dev/chipsee-gpio1 ~ /dev/chipsee-gpio4 for OUT1 ~ OUT4
        """
        is_valid = (outputX in self.outputs) and (value in [GPIO.HIGH, GPIO.LOW])
        return True if is_valid else False

