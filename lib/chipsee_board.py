import json

class ChipseeBoard(object):
    """
    This class aims to detect what Chipsee board this app is running on,
    and the Linux file path of its peripherals.

    It works by reading the `/proc/device-tree/compatible` file on Linux,
    then check the keyword that MAY exist in that file.

    If a board ID is successfully detected and supported, this class will then read
    the available peripherals (eg: Screen brightness, GPIO, Serials ports)
    Linux file path into a dict from a JSON file in the `config/peripherals` folder.
    """
    def __init__(self):
        self.name = None
        self.detect()
        self.read_peripheral_config()

    def detect(self):
        desc = self.read_board_info()
        if desc is None:
            self.id = None
            self.name = None
            return

        if "bcm2711" in desc:
            self.id = "CS10600RA4070"
            self.name = "cm4"
        elif "px30" in desc:
            self.id = "CS12800PX101A"
            self.name = "px30"
        else:
            self.id = None
            self.name = None

    def read_board_info(self):
        try:
            with open("/proc/device-tree/compatible") as f:
                return f.readline()
        except FileNotFoundError:
            return None

    def read_peripheral_config(self):
        if self.id is None:
            self.peripherals = {}
            return
        with open("config/peripherals/{}.json".format(self.id)) as f:
            self.peripherals = json.load(f)

    def devices(self):
        return self.peripherals


board = ChipseeBoard()
