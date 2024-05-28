# test serial connection using Python client

import serial

port_name = '/dev/ttys004'  
ser = serial.Serial(port_name, baudrate=9600)

while True:
    data = ser.read_until(b'\r').decode().strip()
    print(data)
    
ser.close()