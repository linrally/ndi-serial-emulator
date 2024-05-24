# In terminal, create a virtual serial port pair
# socat -d -d pty,raw,echo=1 pty,raw,echo=1

import serial

port_name = '/dev/ttys021'  
ser = serial.Serial(port_name, baudrate=9600)

print(f"Beginning connection on {port_name}")

ErrorCode = 0

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

def append_crc16(reply):
    crc16 = [0]
    for i, ch in enumerate(reply): 
        calc_crc16(ord(ch), crc16)
    return f"{reply}{crc16[0]:04X}\r"

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
        set_error(NDI_BAD_COMM)
        return -1

port_handles = {}

# PHSR handle types
NDI_ALL_HANDLES = 0x00
NDI_STALE_HANDLES = 0x01
NDI_UNINITIALIZED_HANDLES = 0x02
NDI_UNENABLED_HANDLES = 0x03
NDI_ENABLED_HANDLES = 0x04

def get_handle_status(handle):
    bits = 0
    if handle.get("occupied"):
        bits |= 1 << 11
    if handle.get("initialized"):
        bits |= 1 << 7
    if handle.get("enabled"):
        bits |= 1 << 6
    return bits

def PHSR_helper(command): # UNTESTED
    reply_option = int(command[5:7], 16)

    filtered_handles = {}
    if reply_option == NDI_UNENABLED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handles.items() 
            if value.get("occupied") and not (value.get("initialized") or value.get("enabled"))
        }
    elif reply_option == NDI_UNINITIALIZED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handles.items() 
            if value.get("occupied") and value.get("initialized") and not value.get("enabled")
        }
    elif reply_option == NDI_ENABLED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handles.items() 
            if value.get("enabled")
        }
        
    reply = f"{len(filtered_handles):02X}"
    for key, value in filtered_handles.items():
       reply += f"{key:02X}{get_handle_status(value):03X}"

    serial_write(append_crc16(reply))

    return 0

def PHRQ_helper(command):
    device = command[5:13]
    system_type = command[13]
    tool_type = command[14]
    port_number = command[15:17]
    reserved =command[17:19]

    i = 0x00
    while i in port_handles:
        i += 1

    port_handles[i] = {
        'occupied': False,
        'initialized': False,
        'enabled': False,
        'rom' : bytearray(b'\x00' * 1024) # 1 kB
    }

    serial_write(append_crc16(f"{i:02X}"))

    return 0

def PVWR_helper(command):
    port_handle = int(command[5:7], 16)
    address = int(command[7:11], 16)
    data = bytearray.fromhex(command[11:11+128])
    
    handle = port_handles[port_handle]
    handle['rom'][address:address+64] = data # 64 bytes of data
    handle['occupied'] = True # A port becomes occupied after first 64 bytes of data are written

    serial_write(append_crc16("OKAY"))

    return 0

def set_error(errnum):
    ErrorCode = errnum
    return errnum; 

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
        set_error(NDI_BAD_CRC)
        serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))

    code, args = rec_command.split(":") # Args are unused

    if code == "COMM":
        if(COMM_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "PHSR": 
       if(PHSR_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "PHRQ":
       if(PHRQ_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "PVWR":
       if(PVWR_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))