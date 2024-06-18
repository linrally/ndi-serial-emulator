# USAGE: 
# In terminal, create a virtual serial port pair
# socat -d -d pty,raw,echo=1 pty,raw,echo=1

# TODO: 
# (low prio) Clean up append_crc16 function
# what if error but old errorcode
# 0x0D, 0x0E, 0x0F errors (port handles)
# 0x02, 0x03 errors (general)
# serial timeout with error

import serial
import time
import struct
import argparse

parser = argparse.ArgumentParser(description='Emulator script for serial communication.')
parser.add_argument('--port', required=True, type=str, help='name of the port to connect to')
args = parser.parse_args()
port_name = args.port # /dev/ttys035

ser = serial.Serial(port_name, baudrate=9600) 
print(f"Beginning connection on {port_name}")

ErrorCode = 0

# ERROR CODES
NDI_INVALID = 0x01
NDI_BAD_CRC = 0x04
NDI_BAD_COMM = 0x06

isTracking = False
start_time = time.time()
frame_number = 0

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

# PHRQ REPLY OPTIONS
NDI_ALL_HANDLES = 0x00              # return all handles
NDI_STALE_HANDLES = 0x01            # only handles waiting to be freed
NDI_UNINITIALIZED_HANDLES = 0x02    # handles needing initialization
NDI_UNENABLED_HANDLES = 0x03        # handles needing enabling
NDI_ENABLED_HANDLES = 0x04          # handles that are enabled

def get_port_status(handle):
    bits = 0
    if handle.get("occupied"):
        bits |= 1 
    if handle.get("initialized"):
        bits |= 1 << 4
    if handle.get("enabled"):
        bits |= 1 << 5
    return bits

def PHSR_helper(command): 
    reply_option = int(command[5:7], 16)

    filtered_handles = {}
    if reply_option == NDI_UNINITIALIZED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handles.items() 
            if value.get("occupied") and not (value.get("initialized") or value.get("enabled"))
        }
    elif reply_option == NDI_UNENABLED_HANDLES:
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
       reply += f"{key:02X}{get_port_status(value):03X}"

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

def PINIT_helper(command):
    port_handle = int(command[6:8], 16)
    
    handle = port_handles[port_handle]
    handle['initialized'] = True

    serial_write(append_crc16("OKAY"))  

    return 0

def PENA_helper(command):
    port_handle = int(command[5:7], 16)
    tracking_priority = command[7]

    handle = port_handles[port_handle]
    handle['enabled'] = True

    serial_write(append_crc16("OKAY"))

    return 0

def TSTART_helper(command):
    reply_option = command[6:8] if len(command) >= 8 else None # fix this option

    global isTracking 
    isTracking = True

    serial_write(append_crc16("OKAY")) 

    return 0

# BX REPLY OPTIONS
NDI_XFORMS_AND_STATUS = 0x0001  # transforms and status
NDI_ADDITIONAL_INFO = 0x0002    # additional tool transform info
NDI_SINGLE_STRAY = 0x0004       # stray active marker reporting
NDI_FRAME_NUMBER = 0x0008       # frame number for each tool
NDI_PASSIVE = 0x8000            # report passive tool information
NDI_PASSIVE_EXTRA = 0x2000      # add 6 extra passive tools
NDI_PASSIVE_STRAY = 0x1000      # stray passive marker reporting 

def BX_helper(command): 
    reply_option = int(command[3:7], 16) if len(command) >= 7 else NDI_XFORMS_AND_STATUS

    body_bytes = bytearray()
    body_bytes.extend(struct.pack("<B", len(port_handles)))
    
    for key, value in port_handles.items():        
        body_bytes.extend(struct.pack("<b", key))

        # handle status
        if value['enabled']:  # valid
            body_bytes.extend(struct.pack("<b", 1))
        else: # disabled
            body_bytes.extend(struct.pack("<b", 4))
            continue
        
        reply_option_bytes = bytearray()

        if reply_option & NDI_XFORMS_AND_STATUS:
            Qo, Qx, Qy, Qz = 1, 0, 0, 0
            Tx, Ty, Tz = 0, 0, 0
            rms_error = 0

            reply_option_bytes.extend(struct.pack("<ffff", Qo, Qx, Qy, Qz))
            reply_option_bytes.extend(struct.pack("<fff", Tx, Ty, Tz))
            reply_option_bytes.extend(struct.pack("<f", rms_error))
            reply_option_bytes.extend(struct.pack("<I", get_port_status(value)))
            reply_option_bytes.extend(struct.pack("<I", frame_number))

        body_bytes.extend(reply_option_bytes)
        body_bytes.extend(struct.pack("<H", 0)) # system status 

    header_bytes = bytearray.fromhex("C4A5")
    header_bytes.extend(struct.pack("<H", len(body_bytes))) # reply length

    header_crc16 = [0]
    for i, by in enumerate(header_bytes): 
        calc_crc16(by, header_crc16)
    
    body_crc16 = [0]
    for i, by in enumerate(body_bytes): 
        calc_crc16(by, body_crc16)

    reply = header_bytes + struct.pack("<H", header_crc16[0]) + body_bytes + struct.pack("<H", body_crc16[0])
    serial_write_binary(reply)

    return 0

def set_error(errnum):
    global ErrorCode 
    ErrorCode = errnum
    return errnum; 

def serial_write(reply):
    ser.write(reply.encode())
    print(f"Sent: {reply}")

def serial_write_binary(reply):
    ser.write(reply)
    print(f"Sent binary: {reply.hex()}")

while True:
    data = ser.read_until(b'\r').decode().strip()
    print(f"Recieved: {data}")

    frame_number = int((time.time() - start_time) * 60)
    
    # Initialization (probably needs to be modified at some point to remove hardcoding)
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
    elif code == "PENA":
        if(PENA_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "PINIT":
        if(PINIT_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "TSTART":
        if(TSTART_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    elif code == "BX":
        if(BX_helper(rec_command) != 0):
            serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))
    else:
        set_error(NDI_INVALID)
        serial_write(append_crc16(f"ERROR:{ErrorCode}\r"))