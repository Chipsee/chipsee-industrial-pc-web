from lib.chipsee_board import board

from pymodbus.version import version
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.server.sync import ModbusSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from pymodbus.transaction import ModbusRtuFramer

# Logging is extremely handy for debugging modbus, uncomment the following if you encounter weird bugs.

# import logging
# FORMAT = ('%(asctime)-15s %(threadName)-15s'
#           ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

            
class ModbusServerSync(object):
    """
    Reference: https://github.com/riptideio/pymodbus/blob/v2.5.3/pymodbus/server/sync.py
    params:
    - comm: Communication method: TCP or Serial.
            (For TLS, Udp, Ascii, Binary: Check the docs, not hard to implement.)
    - emit_to: Websocket instance. When modbus server receives message, it forwards it to 
                websocket, to display the message on the web page.
    - serial_device_name: name of chipsee board serial device assigned 
                        in config/{chipsee_board_id}.json, e.g: 'rs485'.
    """
    def __init__(self, comm, emit_to=None, serial_device_name=None):
        self.comm = comm
        self.closed = True # server status
        self.emit_to = emit_to # websocket instance
        self.websocket_name = "modbus_server" # websocket ID
        if serial_device_name:
            self.serial_address = board.devices().get(serial_device_name)
        self.tcp_address_ip = "0.0.0.0"
        self.tcp_address_port = 5020
            
    
    def stop(self):
        """Stop the server"""
        if self.comm == "tcp":
            self.server.shutdown()
        self.server.server_close()
        self.closed = True
            
    def run_server(self):
        # In-memory data store of a Modbus server, like those coils and registers in PLCs.
        store = ModbusSlaveContext(
            di=CustomDataBlock(self.emit_to, [17]*100),
            co=CustomDataBlock(self.emit_to, [17]*100),
            hr=CustomDataBlock(self.emit_to, [17]*100),
            ir=CustomDataBlock(self.emit_to, [17]*100)
        )
        context = ModbusServerContext(slaves=store, single=True)

        # initialize the server information
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'Example'
        identity.ProductCode = 'PM'
        identity.VendorUrl = 'https://chipsee.com'
        identity.ProductName = 'Example Modbus Server'
        identity.ModelName = 'Example Modbus Server'
        identity.MajorMinorRevision = version.short()

        # run the server
        # TCP with different framer
        if self.comm == "tcp":
            try:
                if self.emit_to is not None:
                    msg = "Starting a modbus TCP server on {}:{}".format(self.tcp_address_ip, self.tcp_address_port)
                    self.emit_to.emit(self.websocket_name, { 'data':  msg })
                # print(msg)
                self.server = ModbusTcpServer(
                    context, 
                    identity=identity, 
                    framer=ModbusRtuFramer, 
                    address=(self.tcp_address_ip, self.tcp_address_port)
                )
            except OSError:
                if self.emit_to is not None:
                    msg = "Port {} is occupied, will start on port {}".format(self.tcp_address_port, self.tcp_address_port+1)
                    self.emit_to.emit(self.websocket_name, { 'data':  msg })
                # print(msg)
                if self.tcp_address_port < 65535:
                    self.tcp_address_port += 1
                self.run_server()
        # RTU Serial:
        elif self.comm == "serial":
            if self.emit_to is not None:
                msg = "Starting a modbus Serial RTU server on {}".format(self.serial_address)
                self.emit_to.emit(self.websocket_name, { 'data':  msg })
            self.server = ModbusSerialServer(
                context, 
                identity=identity, 
                framer=ModbusRtuFramer, 
                port=self.serial_address, 
                timeout=0.005, 
                baudrate=115200
            )
        else:
            self.server = None
            return
        if self.server:
            self.closed = False
            self.server.serve_forever()
        

class CustomDataBlock(ModbusSparseDataBlock):
    """ 
    A datablock that stores the new value in memory
    and performs a custom action after it has been stored.
    
    The inherited ModbusSparseDataBlock is supplied with pymodbus lib,
    if you want to do something with modbus client's data,
    use this CustomDataBlock and do what you want in the setValues method.
    
    For this case, it's sending the incoming client data to websocket.
    If you do not wish to do extra steps when client writes a data, 
    just delete this class and use the ModbusSparseDataBlock 
    or other data structures defined in pymodbus.
    Reference: https://pymodbus.readthedocs.io/en/v2.5.3/source/example/custom_datablock.html
    and: https://github.com/riptideio/pymodbus/blob/v2.5.3/pymodbus/datastore/store.py
    """
    def __init__(self, emit_to, values):
        self.emit_to = emit_to # websocket instance
        self.websocket_name = "modbus_server"  # websocket ID
        super().__init__(values)
        
    def getValues(self, address, count=1):
        self.emit_read_to_websocket(address, count)
        return super(CustomDataBlock, self).getValues(address, count)
        
    def setValues(self, address, value):
        # whatever you want to do with the written value is done here,
        # however make sure not to do too much work here or it will
        # block the server, espectially if the server is being written
        # to very quickly
        self.emit_write_to_websocket(address, value)
        super(CustomDataBlock, self).setValues(address, value)

        
    def emit_write_to_websocket(self, address, value):
        if self.emit_to is not None:
            msg = "Modbus: Set value: {} to address: {}".format(value, address)
            # print("Emit ({}) to websocket modbus_recv".format(msg))
            self.emit_to.emit(self.websocket_name, { 'data':  msg })
    
    def emit_read_to_websocket(self, address, count):
        if self.emit_to is not None:
            msg = "Modbus: Get value: count {} from address: {}".format(address, count)
            # print("Emit ({}) to websocket modbus_recv".format(msg))
            self.emit_to.emit(self.websocket_name, { 'data':  msg })