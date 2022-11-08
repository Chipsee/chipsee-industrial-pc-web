import subprocess
class ServerControl(object):
    """
    Use broser button to trigger system functions,
    such as closing the browser, which is useful when browser
    is running at kiosk mode.
    Or reboot/shutdown the server.
    """
    def __init__(self):
        pass
    
    def run(self, cmd):
        if cmd == "close_browser":
            self.close_browser()
        elif cmd == "reboot":
            self.reboot_pc()
        elif cmd == "shutdown":
            self.shutdown_pc()
    
    def close_browser(self):
        subprocess.run(["pkill", "-o", "chromium"])
        
    def reboot_pc(self):
        subprocess.run(["sudo", "reboot"])
        
    def shutdown_pc(self):
        subprocess.run(["sudo", "shutdown", "-h", "now"])