from lib.chipsee_board import board

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.exceptions import ConnectionException
# Logging is extremely handy for debugging modbus, uncomment the following if you encounter weird bugs.

# import logging
# FORMAT = ('%(asctime)-15s %(threadName)-15s '
#           '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

class ModbusClientSync(object):
    def __init__(self, comm, emit_to, serial_device_name=None):
        self.emit_to = emit_to
        self.websocket_name = 'modbus_client'
        self.comm = comm
        if serial_device_name:
            self.serial_address = board.devices().get(serial_device_name)
        
    def run_client(self):
        try:
            if self.comm == "tcp":
                with ModbusTcpClient('localhost', port=5020, framer=ModbusRtuFramer) as client:
                    self.connect_and_test(client)
            elif self.comm == "serial":
                # make sure timeout is larger than modbus server's timeout if using a sync modbus server.
                with ModbusSerialClient(method='rtu', port=self.serial_address, timeout=3, baudrate=115200) as client:
                    self.connect_and_test(client)
        except AttributeError as e:
           self.emit("Error: {}. Is your modbus serial server connected?".format(e), "out")
        except ConnectionException as e:
           self.emit("Error: {}. Can you connect to a modbus TCP/Serial server?".format(e), "out")
                      
    
    def emit(self, msg, direction="in"):
        """
        Emit message to websocket.
        params:
        - msg: Text message to push to browser.
        - direction: "in" / "out", affects web page CSS style.
        """
        self.emit_to.emit(self.websocket_name, { 'data': msg, 'direction': direction })
        
    def connect_and_test(self, client):
        client.connect()
        # ------------------------------------------------------------------------#
        # specify slave to query
        # ------------------------------------------------------------------------#
        # The slave to query is specified in an optional parameter for each
        # individual request. This can be done by specifying the `unit` parameter
        # which defaults to `0x00`
        # ----------------------------------------------------------------------- #
        UNIT=0x01
        self.emit("Read coils(0, 1, 0x01)")
        rr = client.read_coils(0, 1, unit=UNIT)
        self.emit(rr.bits, "out")

        # ----------------------------------------------------------------------- #
        # example requests
        # ----------------------------------------------------------------------- #
        # simply call the methods that you would like to use. Note that some modbus
        # implementations differentiate holding/input discrete/coils and as such
        # you will not be able to write to these, therefore the starting values
        # are not known to these tests. Furthermore, some use the same memory
        # blocks for the two sets, so a change to one is a change to the other.
        # Keep both of these cases in mind when testing as the following will
        # _only_ pass with the asynchronous modbus server (check the pymodbus docs).
        # ----------------------------------------------------------------------- #
        self.emit("Write to a coil (0, True, 0x01), read coils(0, 1, 0x01)[0]:")
        rq = client.write_coil(0, True, unit=UNIT)
        rr = client.read_coils(0, 1, unit=UNIT)
        self.emit(rr.bits[0], "out")

        self.emit("Write to multiple coils (1, [True]*8, 0x01), read coils(1, 21, 0x01):")
        rq = client.write_coils(1, [True]*8, unit=UNIT)
        rr = client.read_coils(1, 21, unit=UNIT)
        # If the returned output quantity is not a multiple of eight,
        # the remaining bits in the final data byte will be padded with zeros
        # (toward the high order end of the byte).
        self.emit(rr.bits, "out") # Should be [True]*21, [False]*3

        self.emit("Write to multiple coils (1, [False]*8, 0x01), read coils(1, 8, 0x01):")
        rq = client.write_coils(1, [False]*8, unit=UNIT)
        rr = client.read_coils(1, 8, unit=UNIT)
        self.emit(rr.bits, "out") # Should be [False]*8

        self.emit("Read discrete inputs (0, 8, 0x01):")
        rr = client.read_discrete_inputs(0, 8, unit=UNIT)
        self.emit(rr.bits, "out")

        self.emit("Write to a holding register (1, 10, 0x01), read holding registers(1, 1, 0x01)[0]:")
        rq = client.write_register(1, 10, unit=UNIT)
        rr = client.read_holding_registers(1, 1, unit=UNIT)
        self.emit(rr.registers[0], "out") # should be 10

        self.emit("Write to multiple holding registers (1, [10]*8, 0x01), read holding registers(1, 8, 0x01):")
        rq = client.write_registers(1, [10]*8, unit=UNIT)
        rr = client.read_holding_registers(1, 8, unit=UNIT)
        self.emit(rr.registers, "out") # should be [10]*8

        self.emit("Read input registers (1, 8, 0x01):")
        rr = client.read_input_registers(1, 8, unit=UNIT)
        self.emit(rr.registers, "out") # should be 8

        arguments = {
            'read_address':    1,
            'read_count':      8,
            'write_address':   1,
            'write_registers': [20]*8,
        }
        self.emit("Read write registers simulataneously (0x01, 1, 8, 1, [20]*8):")
        rq = client.readwrite_registers(unit=UNIT, **arguments)
        self.emit(rq.registers, "out") # should be [20]*8
        self.emit("Read holding registers (1, 8, 0x01):")
        rr = client.read_holding_registers(1, 8, unit=UNIT)
        self.emit(rr.registers, "out") # should be [20]*8

        # close the client
        client.close()
