# test serial connection using Python client

import serial

port_name = '/dev/ttys004'  
ser = serial.Serial(port_name, baudrate=9600)

while True:
    try:
        ser.write("INIT:E3A5\r".encode())
    except KeyboardInterrupt:
        print("Exiting...")
        break

ser.close()