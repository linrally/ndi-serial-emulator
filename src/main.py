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

all_landmarks = {
    0x01: [
        {
            'frame_number': 0,
            'quaternion' : [1, 0, 0, 0],
            'transform' : [0, 0, -750],
            'rms_error' : 0,
        },
        {
            'frame_number': 450,
            'quaternion' : [1, 0, 0, 0],
            'transform' : [0, 0, -1000],
            'rms_error' : 0,
        },
        {
            'frame_number': 900,
            'quaternion' : [1, 0, 0, 0],
            'transform' : [0, 0, -750],
            'rms_error' : 0,
        },
    ]
}
pl = PoseLoader(all_landmarks)

frm.start()
while True:
    frm.update()

    for handle_id in all_landmarks.keys():
        tf = pl.get_transform(handle_id, frm.frame_number % 900)
        prt.load_transform(handle_id, tf)
    
    rx_bytes = ser.read_data()

    if rx_bytes.endswith(b'\0'):
        COMMANDS['RESET'].execute(None)
        continue

    if rx_bytes.endswith(b'\r'):
        command, args, crc_int = ser.parse_rx
        if command in COMMANDS:
            COMMANDS[command].execute(args)
        else:
            err.set(NDI_INVALID)
            ser.send_reply(f"ERROR:{err.ErrorCode}", debug=True)