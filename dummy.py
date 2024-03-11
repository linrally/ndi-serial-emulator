# test serial connection using Python client

import serial

port_name = '/dev/ttys015'  
ser = serial.Serial(port_name, baudrate=9600)

while True:
    try:
        ser.write("Hello".encode())
    except KeyboardInterrupt:
        print("Exiting...")
        break

ser.close()