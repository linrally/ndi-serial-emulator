import re
from config import *
from crc import CRC
from serialmanager import SerialManager
from porthandlemanager import PortHandleManager
from errormanager import ErrorManager
from framemanager import FrameManager
from poseloader import PoseLoader
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

landmarks = [
    {
        'frame_number': 0,
        'quaternion' : [1, 0, 0, 0],
        'transform' : [0, 0, 0],
        'rms_error' : 0,
    },
    {
        'frame_number': 120,
        'quaternion' : [1, 0, 0, 0],
        'transform' : [50, 0, 0],
        'rms_error' : 0,
    },
    {
        'frame_number': 240,
        'quaternion' : [1, 0, 0, 0],
        'transform' : [50, 50, 50],
        'rms_error' : 0,
    }
]
pl = PoseLoader()
pl.generate(landmarks=landmarks)

frm.start()
while True:
    frm.update()
    prt.load_transform(0x00, pl.get_transform(frm.frame_number))
    rx_bytes = ser.read_data()

    if rx_bytes.endswith(b'\0'):
        COMMANDS['RESET'].execute(None)
        continue

    if rx_bytes.endswith(b'\r'):
        command, args, crc_int = parse_rx(rx_bytes)
        if command in COMMANDS:
            COMMANDS[command].execute(args)
        else:
            err.set(NDI_INVALID)
            ser.send_reply(f"ERROR:{err.ErrorCode}", debug=True)