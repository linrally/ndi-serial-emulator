import serial

# in terminal, create a virtual serial port pair
# socat -d -d pty,raw,echo=1 pty,raw,echo=1

port_name = '/dev/ttys005'  
ser = serial.Serial(port_name, baudrate=9600)

print(f"Beginning connection on {port_name}")

def serial_write(response):
    ser.write(response.encode())
    print(f"Sent: {response}")

while True:
    try:   
        data = ser.read_until(b'\r').decode()
        print(f"Recieved: {data}")
        match data.strip():
            case "INIT:E3A5":
                serial_write("OKAYA896\r")
            case "GETINFO:Features.Firmware.Version0492":
                serial_write("Features\r")
    except KeyboardInterrupt:
        print("Exiting...")
        break

# which port should we send data to?
# read from?

ser.close()