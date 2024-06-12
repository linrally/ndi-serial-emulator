import serial
import time
import re
from config import *
import struct

port_name = "/dev/cu.usbserial-AB0NSEDF"
ser = serial.Serial(port_name, baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=None)
print(f"Beginning connection on {port_name}")

ErrorCode = 0 # TODO: Implement error handling

def set_error(errnum):
    global ErrorCode 
    ErrorCode = errnum
    return errnum; 

def calc_crc16_int(byte_data): 
    # Translated from C code at https://stackoverflow.com/a/68095008
    crc = 0x0000
    for i in (range(0, len(byte_data))):
        crc ^= byte_data[i]
        for k in range(0, 8):
            crc = (crc >> 1) ^ 0xa001 if crc & 1 else crc >> 1
    return crc

def calc_crc16_str(data):
    if isinstance(data, bytes) or isinstance(data, bytearray):
        byte_data = data
    elif isinstance(data, str):
        byte_data = data.encode("utf-8", errors="strict")
    else:
        raise TypeError("Expected data argument to be of type bytes, bytearray, or str")
    return calc_crc16_int(byte_data).to_bytes(2, byteorder="big").hex().upper()

def send_reply(data, append_crc=True, append_cr=True, debug=False, binary=False):
    bytes_data = data if binary else data.encode()
    if append_crc:
        bytes_data += calc_crc16_str(bytes_data).encode()
    if append_cr:
        bytes_data += "\r".encode()
    ser.write(bytes_data)
    
    if debug:   
        if binary:
            print(f"Sent: {bytes_data.hex()}")
        else:
            print(f"Sent: {bytes_data}")

    rx_bytes.clear()

def parse_rx(rx_bytes): # TODO: CLEAN UP
    if not rx_bytes.endswith(b'\r'):
        raise RuntimeError("Expected \r at end of rx!")

    command_match = re.match(rb'^[A-Za-z]+[: ]', rx_bytes)
    if command_match is None:
        raise ValueError(f"Error parsing command from '{rx_bytes}'!")

    separator_idx = command_match.end()-1
    separator = rx_bytes[separator_idx:separator_idx+1]
    command = rx_bytes[:separator_idx].decode(encoding="utf-8", errors="strict")

    if separator == b':': # end = 4-byte CRC (ASCII) + 1-byte \r
        body_end_idx = len(rx_bytes) - 5
        rx_body_bytes, rx_crc_ascii = rx_bytes[:body_end_idx], rx_bytes[body_end_idx:-1]
        rx_crc_int = int(rx_crc_ascii, 16)
        calc_crc_int = calc_crc16_int(rx_body_bytes)
        if rx_crc_int != calc_crc_int:
            raise ValueError(f"Received CRC 0x{rx_crc_int:X} doesn't match calculated CRC 0x{calc_crc_int:X} for message \"{rx_bytes}\"")
    elif separator == b' ': # end = 1-byte \r (NO CRC)
        body_end_idx = len(rx_bytes) - 1
    else:
        raise RuntimeError(f"Expected separator to either be ':' or ' ', but got '{separator}'!")

    args = rx_bytes[separator_idx + 1:body_end_idx].decode(encoding="utf-8", errors="strict")

    return command, args, rx_crc_int

def RESET():
    ser.flush()
    time.sleep(0.01 * ser.out_waiting)

    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE

    rx_bytes.clear()
    send_reply("RESET", debug=True)
    return 0

def INIT():
    send_reply("OKAY", debug=True)
    return 0

def VER():
    send_reply(VER_STR_CUSTOM, debug=True)
    return 0

def COMM(command):
    CONVERT_BAUD = [9600, 14400, 19200, 38400, 57600, 115200, 921600, 1228739]
    newspeed = 9600
    newdps = "8N1"
    newhand = 0 # Handshaking parsed, but not implemented

    send_reply("OKAY", debug=True) # TODO: Error should be returned before the baud change
    time.sleep(0.05) # Delay to allow buffer to clear before changing baud rate

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

def APIREV():
    send_reply(APIREV_STR, debug=True)
    return 0    

def GET(key):
    matching_attrs = [line for line in GET_ATTRS.split("\n") if re.search(key, line.split("=")[0]) is not None]
    if len(matching_attrs) == 0:
        set_error(NDI_NO_USER_PARAM)
        return -1
    send_reply("\n".join(matching_attrs), debug=True)
    return 0

def SFLIST(args): 
    reply_option = int(args[0:2], 16)
    if reply_option == 0x02:
        send_reply("6", debug=True)
    return 0

def TSTART():
    # TODO: implement alt reply option
    global isTracking 
    isTracking = True
    send_reply("OKAY", debug=True)
    return 0

def BX(command): # TODO: Check for isTracking and throw error
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

    reply = header_bytes + struct.pack("<H", calc_crc16_int(header_bytes)) + body_bytes + struct.pack("<H", calc_crc16_int(body_bytes))
    send_reply(reply, debug=True, append_crc=False, append_cr=False, binary=True)

    return 0

def TSTOP():
    global isTracking 
    isTracking = False
    send_reply("OKAY", debug=True)
    return 0

def get_port_status(handle):
    bits = 0
    if handle.get("occupied"):
        bits |= 1 
    if handle.get("initialized"):
        bits |= 1 << 4
    if handle.get("enabled"):
        bits |= 1 << 5
    return bits

def PHRQ(command):
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

    send_reply(f"{i:02X}", debug=True)

    return 0

def PHSR(command): 
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

    send_reply(reply, debug=True)

    return 0

def PVWR(command):
    port_handle = int(command[5:7], 16)
    address = int(command[7:11], 16)
    data = bytearray.fromhex(command[11:11+128])
    
    handle = port_handles[port_handle]
    handle['rom'][address:address+64] = data # 64 bytes of data
    handle['occupied'] = True # A port becomes occupied after first 64 bytes of data are written

    send_reply("OKAY", debug=True)

    return 0

def PINIT(command):
    port_handle = int(command[6:8], 16)
    
    handle = port_handles[port_handle]
    handle['initialized'] = True

    send_reply("OKAY", debug=True)

    return 0

def PENA(command):
    port_handle = int(command[5:7], 16)
    tracking_priority = command[7]

    handle = port_handles[port_handle]
    handle['enabled'] = True

    send_reply("OKAY", debug=True)

    return 0

def PDIS(command):
    port_handle = int(command[5:7], 16)

    handle = port_handles[port_handle]
    handle['enabled'] = False

    send_reply("OKAY", debug=True)

    return 0

rx_bytes = bytearray()

isTracking = False
start_time = time.time()
frame_number = 0

port_handles = {} # TODO: Make into a class?

while True:
    frame_number = int((time.time() - start_time) * 60)

    # Read and print decoded byte data
    while ser.in_waiting > 0:
        b = ser.read(1)
        rx_bytes.extend(b)
        
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

    if rx_bytes.endswith(b'\0'):
        RESET()
        continue

    if rx_bytes.endswith(b'\r'):
        command, args, crc_int = parse_rx(rx_bytes)
        if command == "INIT":
            INIT()
        elif command == "VER":
            VER()
        elif command == "COMM":
            COMM(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "APIREV":
            APIREV()
        elif command == "GET":
            GET(args)
        elif command == "SFLIST":
            SFLIST(args)
        elif command == "TSTART":
            TSTART()
        elif command == "BX":
            time.sleep(0.5)
            BX(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "TSTOP":
            TSTOP()
        elif command == "PHRQ":
            PHRQ(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "PHSR":
            PHSR(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "PVWR":
            PVWR(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "PENA":
            PENA(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "PDIS":
            PDIS(rx_bytes.decode()) # TODO: make consistent with args?
        elif command == "PINIT":
            PINIT(rx_bytes.decode()) # TODO: make consistent with args?
        else:
            set_error(NDI_INVALID)
            send_reply(f"ERROR:{ErrorCode}", debug=True)

# TODO: Checking enable and then unchecking it results ina communication error (PDIS is not called ? why)
# TODO: clean up files in the folder
# TODO: put all the functions in another class?