import serial
import time
import re
from config import *
from crc import CRC
from serial_manager import SerialManager
from port_handle_manager import PortHandleManager
import struct

port_name = "/dev/cu.usbserial-AB0NSEDF"
serial_manager = SerialManager(port_name)

ErrorCode = 0 # TODO: Implement error handling

def set_error(errnum):
    global ErrorCode 
    ErrorCode = errnum
    return errnum; 

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
        calc_crc_int = CRC.calc_crc16_int(rx_body_bytes)
        if rx_crc_int != calc_crc_int:
            raise ValueError(f"Received CRC 0x{rx_crc_int:X} doesn't match calculated CRC 0x{calc_crc_int:X} for message \"{rx_bytes}\"")
    elif separator == b' ': # end = 1-byte \r (NO CRC)
        body_end_idx = len(rx_bytes) - 1
    else:
        raise RuntimeError(f"Expected separator to either be ':' or ' ', but got '{separator}'!")

    args = rx_bytes[separator_idx + 1:body_end_idx].decode(encoding="utf-8", errors="strict")

    return command, args, rx_crc_int

def RESET():
    serial_manager.reset()
    serial_manager.send_reply("RESET", debug=True)
    return 0

def INIT():
    serial_manager.send_reply("OKAY", debug=True)
    return 0

def VER():
    serial_manager.send_reply(VER_STR_CUSTOM, debug=True)
    return 0

def COMM(command):
    CONVERT_BAUD = [9600, 14400, 19200, 38400, 57600, 115200, 921600, 1228739]
    newspeed = 9600
    newdps = "8N1"
    newhand = 0 # Handshaking parsed, but not implemented

    serial_manager.send_reply("OKAY", debug=True) # TODO: Error should be returned before the baud change
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
        serial_manager.ser.baudrate = newspeed
        
        if newdps[1] == "N":
           serial_manager.ser.parity = serial.PARITY_NONE
        elif newdps[1] == "O":
           serial_manager.ser.parity = serial.PARITY_ODD
        elif newdps[1] == "E":
           serial_manager.ser.parity = serial.PARITY_EVEN
        
        if newdps[0] == '7':
            serial_manager.ser.bytesize = serial.SEVENBITS
        elif newdps[0] == '8':
            serial_manager.ser.bytesize = serial.EIGHTBITS

        if newdps[2] == '1':
            serial_manager.ser.stopbits = serial.STOPBITS_ONE
        elif newdps[2] == '2':
            serial_manager.ser.stopbits = serial.STOPBITS_TWO

        return 0
    except:
        set_error(NDI_BAD_COMM)
        return -1

def APIREV():
    serial_manager.send_reply(APIREV_STR, debug=True)
    return 0    

def GET(key):
    matching_attrs = [line for line in GET_ATTRS.split("\n") if re.search(key, line.split("=")[0]) is not None]
    if len(matching_attrs) == 0:
        set_error(NDI_NO_USER_PARAM)
        return -1
    serial_manager.send_reply("\n".join(matching_attrs), debug=True)
    return 0

def SFLIST(args): 
    reply_option = int(args[0:2], 16)
    if reply_option == 0x02:
        serial_manager.send_reply("6", debug=True)
    return 0

def TSTART():
    # TODO: implement alt reply option
    global isTracking 
    isTracking = True
    serial_manager.send_reply("OKAY", debug=True)
    return 0

def BX(command): # TODO: Check for isTracking and throw error
    reply_option = int(command[3:7], 16) if len(command) >= 7 else NDI_XFORMS_AND_STATUS

    body_bytes = bytearray()
    body_bytes.extend(struct.pack("<B", len(port_handle_manager.port_handles)))
    
    for key, value in port_handle_manager.port_handles.items():        
        body_bytes.extend(struct.pack("<b", key))

        # handle status
        if value['enabled']:  # valid
            body_bytes.extend(struct.pack("<b", 1))
        else: # disabled
            body_bytes.extend(struct.pack("<b", 4))
            continue
        
        reply_option_bytes = bytearray()

        if reply_option & NDI_XFORMS_AND_STATUS:
            Qo, Qx, Qy, Qz = 1, 0, 0, 0 # store in port handles and grab the value
            Tx, Ty, Tz = 0, 0, -750
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

    reply = header_bytes + struct.pack("<H", CRC.calc_crc16_int(header_bytes)) + body_bytes + struct.pack("<H", CRC.calc_crc16_int(body_bytes))
    serial_manager.send_reply(reply, debug=True, append_crc=False, append_cr=False, binary=True)

    return 0

def TSTOP():
    global isTracking 
    isTracking = False
    serial_manager.send_reply("OKAY", debug=True)
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

    port_handle = port_handle_manager.create_handle()
    serial_manager.send_reply(f"{port_handle:02X}", debug=True)

    return 0

def PHSR(command): 
    reply_option = int(command[5:7], 16)

    filtered_handles = {}
    if reply_option == NDI_UNINITIALIZED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handle_manager.port_handles.items() 
            if value.get("occupied") and not (value.get("initialized") or value.get("enabled"))
        }
    elif reply_option == NDI_UNENABLED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handle_manager.port_handles.items() 
            if value.get("occupied") and value.get("initialized") and not value.get("enabled")
        }
    elif reply_option == NDI_ENABLED_HANDLES:
        filtered_handles = {
            key: value 
            for key, value in port_handle_manager.port_handles.items() 
            if value.get("enabled")
        }
        
    reply = f"{len(filtered_handles):02X}"
    for key, value in filtered_handles.items():
       reply += f"{key:02X}{get_port_status(value):03X}"

    serial_manager.send_reply(reply, debug=True)

    return 0

def PVWR(command):
    port_handle = int(command[5:7], 16)
    address = int(command[7:11], 16)
    data = bytearray.fromhex(command[11:11+128])
    port_handle_manager.write_to_rom(port_handle, address, data)
    serial_manager.send_reply("OKAY", debug=True)
    return 0

def PINIT(command):
    port_handle = int(command[6:8], 16)
    port_handle_manager.initialize_handle(port_handle)
    serial_manager.send_reply("OKAY", debug=True)

    return 0

def PENA(command):
    port_handle = int(command[5:7], 16)
    tracking_priority = command[7]
    port_handle_manager.enable_handle(port_handle)
    serial_manager.send_reply("OKAY", debug=True)
    return 0

def PDIS(command):
    port_handle = int(command[5:7], 16)
    port_handle_manager.disable_handle(port_handle)
    serial_manager.send_reply("OKAY", debug=True)
    return 0

def PHF(command):
    port_handle = int(command[4:6], 16)
    port_handle_manager.delete_handle(port_handle)
    serial_manager.send_reply("OKAY", debug=True)
    return 0

isTracking = False
start_time = time.time()
frame_number = 0

port_handle_manager = PortHandleManager() # needs some work

while True:
    frame_number = int((time.time() - start_time) * 60)

    rx_bytes = serial_manager.read_data()

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
        elif command == "PHF":
            PHF(rx_bytes.decode()) # TODO: make consistent with args?
        else:
            set_error(NDI_INVALID)
            serial_manager.send_reply(f"ERROR:{ErrorCode}", debug=True)