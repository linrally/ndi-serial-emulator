import serial
import time
from crc import CRC

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