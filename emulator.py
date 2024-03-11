import serial

# in terminal, create a virtual serial port pair
# socat -d -d pty,raw,echo=0 pty,raw,echo=0

port_name = '/dev/ttys014'  
ser = serial.Serial(port_name, baudrate=9600)

while True:
    try:   
        data = ser.read_until(b'\r').decode()
        if data.strip() == "INIT:E3A5\r":
            response = "OKAYA896\r"
            ser.write(response.encode())
            print(f"Sent: {response}")
    except KeyboardInterrupt:
        print("Exiting...")
        break

ser.close()