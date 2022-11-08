import os
import json
import subprocess

from lib.chipsee_board import board

class Brightness:
    def __init__(self):
        self.device = board.devices().get("brightness")
        if self.device is None:
            print("Brightness: cannot find brightness device in config file, buzzer not initialized.")
            return
        self.max_brightness_f = os.path.join(self.device, "max_brightness")
        self.actual_brightness_f = os.path.join(self.device, "actual_brightness")
        self.brightness_f = os.path.join(self.device, "brightness")
        self.give_linux_permission()
        self.init_max_brightness()

    def get_actual_brightness(self):
        if self.device is None:
            return 0

        with open(self.actual_brightness_f, 'r') as f:
            return f.read()

    def set_brightness(self, brightness):
        if self.device is None:
            return 0

        _b = int(brightness)
        if _b < 1:
            _b = 1
        if _b > self.max_brightness:
            _b = self.max_brightness
        brightness = str(_b)
        with open(self.brightness_f, 'w') as f:
            return f.write(brightness)

    def init_max_brightness(self):
        with open(self.max_brightness_f, 'r') as f:
            self.max_brightness = int(f.read())

    def give_linux_permission(self):
        """
        Some Industrial PC doesn't allow write permission of brightness file, like PX30.
        This method gives write permission of backlight brightness Linux file to the user running this program.
        """
        if self.device is None:
            return
        subprocess.run(["sudo", "chmod", "a+w", self.brightness_f])