# in terminal, create a virtual serial port pair
# socat -d -d pty,raw,echo=1 pty,raw,echo=1

import serial

port_name = '/dev/ttys007'  
ser = serial.Serial(port_name, baudrate=9600)

print(f"Beginning connection on {port_name}")

NDI_BAD_CRC = 0x04
NDI_BAD_COMM = 0x06

def calc_crc16(data, pu_crc16):
    ODD_PARITY = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]
    data = (data ^ (pu_crc16[0] & 0xff)) & 0xff
    pu_crc16[0] >>= 8
    if ODD_PARITY[data & 0x0f] ^ ODD_PARITY[data >> 4]:
        pu_crc16[0] ^= 0xc001
    data <<= 6
    pu_crc16[0] ^= data
    data <<= 1
    pu_crc16[0] ^= data

def COMM_helper(command):
    CONVERT_BAUD = [9600, 14400, 19200, 38400, 57600, 115200, 921600, 1228739]
    newspeed = 9600
    newdps = "8N1"
    newhand = 0 # Handshaking parsed, but not implemented

    if (command[5] >= '0' and command[5] <= '7') or command[5] == 'A':
      if command[5] != 'A':
        newspeed = CONVERT_BAUD[int(command[5])]
      else:
        newspeed = 230400
    if command[6] == '1':
      newdps[0] = '7'
    if command[7] == '1':
      newdps[1] = 'O'
    elif command[7] == '2':
      newdps[1] = 'E'
    if command[8] == '1':
      newdps[2] = '2'
    if command[9] == '1':
      newhand = 1
    
    try:
        ser.baudrate = newspeed
        
        if newdps[1] == "N":
           ser.parity = serial.PARITY_NONE
        elif newdps[1] == "O":
           ser.parity = serial.PARITY_ODD
        elif newdps[1] == "E":
           ser.parity = serial.PARITY_EVEN
        
        if newdps[0] == '7':
            ser.bytesize = serial.SEVENBITS
        elif newdps[0] == '8':
            ser.bytesize = serial.EIGHTBITS

        if newdps[2] == '1':
           ser.stopbits = serial.STOPBITS_ONE
        elif newdps[2] == '2':
            ser.stopbits = serial.STOPBITS_TWO

        return 0
    except:
        return -1

def set_error(errnum):
    reply = f"ERROR{errnum}"
    crc16 = [0]
    for i, ch in enumerate(reply): # Might create a separate function to apply CRC to all replies
        calc_crc16(ord(ch), crc16)
    return f"ERROR{errnum}{crc16[0]:04X}\r" 

def serial_write(response):
    ser.write(response.encode())
    print(f"Sent: {response}")

while True:
    data = ser.read_until(b'\r').decode().strip()
    print(f"Recieved: {data}")
    
    # Initialization
    if data == "INIT:E3A5":
        serial_write("OKAYA896\r")
        continue
    elif data == "GETINFO:Features.Firmware.Version0492": # Required for correct recognition by ndiSerialProbe
        serial_write("Features\r")
        continue

    # Parse command and validate CRC
    rec_command, rec_crc16 = data[:-4], data[-4:]
    crc16 = [0]
    for i, ch in enumerate(rec_command):
        calc_crc16(ord(ch), crc16)
    if(rec_crc16 != f"{crc16[0]:04X}"):
        serial_write(set_error(NDI_BAD_CRC)) 
        continue

    command, args = rec_command.split(":") # Args are unused

    if command == "COMM":
        if(COMM_helper(rec_command) != 0):
            serial_write(set_error(NDI_BAD_COMM))
            continue
    #elif command == "ECHO":

# port dictionary/array
# find the lowest available port not in use
# store ROM data in a string

# BX transform return identity matrix 
# #define ndiPHSR(p,mode) ndiCommand((p),"PHSR:%02X",(mode))

# enabled ports [false, false, false. ...]

# ndiPINIT
# ndiPENA ?

# caching in BX