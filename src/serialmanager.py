import serial
import time
from crc import CRC
import re

class SerialManager:
    def __init__(self, port_name):
        self.ser = serial.Serial(port_name, baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=None)
        print(f"Beginning connection on {port_name}")
        self.rx_bytes = bytearray()
    
    def read_data(self):
        while self.ser.in_waiting > 0:
            b = self.ser.read(1)
            self.rx_bytes.extend(b)
            self._print_received_byte(b)
        return self.rx_bytes
    
    def write_data(self, data):
        self.ser.write(data)

    def reset(self):
        self.ser.flush()
        time.sleep(0.01 * self.ser.out_waiting)
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.rx_bytes.clear()

    def send_reply(self, data, append_crc=True, append_cr=True, debug=False, binary=False):
        bytes_data = data if binary else data.encode()
        if append_crc:
            bytes_data += CRC.calc_crc16_str(bytes_data).encode()
        if append_cr:
            bytes_data += "\r".encode()
        self.write_data(bytes_data)
        
        if debug:   
            if binary:
                print(f"Sent: {bytes_data.hex()}")
            else:
                print(f"Sent: {bytes_data}")

        self.rx_bytes.clear()
    
    def _print_received_byte(self, b): # For debugging purposes
        if b == b'\0':
            print("\\0", end="\n")
        elif b == b'\r':
            print("\\r", end="\n")
        else:
            try:
                pr = b.decode(encoding="utf-8", errors="strict")
            except UnicodeDecodeError:
                pr = "[0x" + b.hex() + "]"
            print(pr, end="")
    
    def parse_rx(self): 
        # TODO: CLEAN UP
        if not self.rx_bytes.endswith(b'\r'):
            raise RuntimeError("Expected \r at end of rx!")

        command_match = re.match(rb'^[A-Za-z]+[: ]', self.rx_bytes)
        if command_match is None:
            raise ValueError(f"Error parsing command from '{self.rx_bytes}'!")

        separator_idx = command_match.end()-1
        separator = self.rx_bytes[separator_idx:separator_idx+1]
        command = self.rx_bytes[:separator_idx].decode(encoding="utf-8", errors="strict")

        if separator == b':': # end = 4-byte CRC (ASCII) + 1-byte \r
            body_end_idx = len(self.rx_bytes) - 5
            rx_body_bytes, rx_crc_ascii = self.rx_bytes[:body_end_idx], self.rx_bytes[body_end_idx:-1]
            rx_crc_int = int(rx_crc_ascii, 16)
            calc_crc_int = CRC.calc_crc16_int(rx_body_bytes)
            if rx_crc_int != calc_crc_int:
                raise ValueError(f"Received CRC 0x{rx_crc_int:X} doesn't match calculated CRC 0x{calc_crc_int:X} for message \"{rx_bytes}\"")
        elif separator == b' ': # end = 1-byte \r (NO CRC)
            body_end_idx = len(self.rx_bytes) - 1
        else:
            raise RuntimeError(f"Expected separator to either be ':' or ' ', but got '{separator}'!")

        args = self.rx_bytes[separator_idx + 1:body_end_idx].decode(encoding="utf-8", errors="strict")

        return command, args, rx_crc_int