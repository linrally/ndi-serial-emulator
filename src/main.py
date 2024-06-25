import re
from config import *
from crc import CRC
from serial_manager import SerialManager
from port_handle_manager import PortHandleManager
from error_manager import ErrorManager
from frame_manager import FrameManager
from commands import COMMANDS_LIST 

port_name = "/dev/cu.usbserial-AB0NSEDF"

ser = SerialManager(port_name)
err = ErrorManager()
prt = PortHandleManager()
frm = FrameManager()

COMMANDS =  {cmd.name: cmd(ser, err, prt, frm) for cmd in COMMANDS_LIST}

def parse_rx(rx_bytes): 
    # TODO: CLEAN UP
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

frm.start()
while True:
    frm.update()
    rx_bytes = ser.read_data()

    if rx_bytes.endswith(b'\0'):
        COMMANDS['RESET'].execute(None)
        continue

    if rx_bytes.endswith(b'\r'):
        command, args, crc_int = parse_rx(rx_bytes)
        if command in COMMANDS:
            COMMANDS[command].execute(args)
        else:
            err.set_error(NDI_INVALID)
            ser.send_reply(f"ERROR:{err.ErrorCode}", debug=True)