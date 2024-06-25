### CABLE CONFIGURATION ###
#
# - Startech Cables in BOTH computers
# OR
# - Startech Cable in iMac, CableMatters Cable in computer running emulator
#
###

import serial
import time
import re

ser = serial.Serial("/dev/cu.usbserial-AB0NSEDF", baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=None)

# translated from C code at https://stackoverflow.com/a/68095008
def calc_crc16_int(bytedata):
    crc = 0x0000
    for i in (range(0, len(bytedata))):
        crc ^= bytedata[i]
        for k in range(0, 8):
            crc = (crc >> 1) ^ 0xa001 if crc & 1 else crc >> 1
    return crc

def calc_crc16_str(data):
    if isinstance(data, bytes) or isinstance(data, bytearray):
        bytedata = data
    elif isinstance(data, str):
        bytedata = data.encode("utf-8", errors="strict")
    else:
        raise TypeError("Expected data argument to be of type bytes, bytearray, or str!")
    return calc_crc16_int(bytedata).to_bytes(2, byteorder="big").hex().upper()

VER_STR_CUSTOM = \
"""Polaris Vicra Control Firmware
NDI S/N: P6-00000
Characterization Date: 06/05/24
Freeze Tag: Polaris Vicra Rev 007.000
Freeze Date: 01/04/10
(C) Northern Digital Inc.
"""

APIREV_STR = "G.001.005"

# TODO: Implement this as a dictionary?
GET_ATTRS = \
"""Cmd.VSnap.Illuminated Frame=0
Cmd.VSnap.Background Frame=0
Cmd.VSnap.Manual Shutter=300
Cmd.VSnap.Frame Types=0
Cmd.VGet.Threshold.Shutter Time=0
Cmd.VGet.Threshold.Trigger=4.98047
Cmd.VGet.Threshold.Background=3.125
Cmd.VGet.Sensor.Color Depth=12
Cmd.VGet.Sensor.Width=768
Cmd.VGet.Sensor.Height=243
Cmd.VGet.Start X=0
Cmd.VGet.End X=767
Cmd.VGet.Color Depth=16
Cmd.VGet.Stride=1
Cmd.VGet.Sample Option=0
Cmd.VGet.Compression=0
Param.User.String0=
Param.User.String1=
Param.User.String2=
Param.User.String3=
Param.User.String4=
Param.Firmware.Current Version=007.000.011
Param.Tracking.Available Volumes=Vicra
Param.Tracking.Selected Volume=0
Param.Tracking.Sensitivity=4
Param.Tracking.Illuminator Rate=0
Param.Default Wavelength.Return Warning=1
Param.Bump Detector.Bump Detection=1
Param.Bump Detector.Clear=0
Param.Bump Detector.Bumped=0
Param.System Beeper=1
Param.Watch Dog Timer=0
Param.Simulated Alerts=0
Param.Host Connection=0
Info.Timeout.INIT=4
Info.Timeout.COMM=2
Info.Timeout.VER=2
Info.Timeout.PHRQ=2
Info.Timeout.PINIT=6
Info.Timeout.PENA=2
Info.Timeout.PDIS=2
Info.Timeout.PHF=2
Info.Timeout.PVWR=2
Info.Timeout.PHSR=2
Info.Timeout.PHINF=2
Info.Timeout.PFSEL=2
Info.Timeout.TSTART=6
Info.Timeout.TSTOP=2
Info.Timeout.TX=4
Info.Timeout.BX=4
Info.Timeout.VSNAP=2
Info.Timeout.VGET=2
Info.Timeout.DSTART=6
Info.Timeout.DSTOP=2
Info.Timeout.IRED=2
Info.Timeout.3D=4
Info.Timeout.PSTART=6
Info.Timeout.PSTOP=2
Info.Timeout.GP=4
Info.Timeout.GETLOG=4
Info.Timeout.SYSLOG=8
Info.Timeout.SFLIST=2
Info.Timeout.VSEL=2
Info.Timeout.SSTAT=2
Info.Timeout.IRATE=2
Info.Timeout.BEEP=2
Info.Timeout.HCWDOG=2
Info.Timeout.SENSEL=2
Info.Timeout.ECHO=2
Info.Timeout.SET=8
Info.Timeout.GET=8
Info.Timeout.GETINFO=15
Info.Timeout.DFLT=2
Info.Timeout.SAVE=8
Info.Timeout.RESET=15
Info.Timeout.APIREV=2
Info.Timeout.GETIO=2
Info.Timeout.SETIO=2
Info.Timeout.LED=2
Info.Timeout.PPRD=4
Info.Timeout.PPWR=4
Info.Timeout.PSEL=2
Info.Timeout.PSRCH=4
Info.Timeout.PURD=4
Info.Timeout.PUWR=4
Info.Timeout.TCTST=2
Info.Timeout.TTCFG=2
Info.Timeout.PSOUT=2
Info.Status.System Mode=Initialized
Info.Status.Alerts=0
Info.Status.New Alerts=0
Info.Status.Alerts Overflow=0
Info.Status.Bump Detected=0
Info.Status.New Log Entry=0
Features.Keys.Installed Keys.0=
Features.Keys.Disabled Keys=
Features.Tools.Enabled Tools=15
Features.Tools.Active Ports=0
Features.Tools.Passive Ports=6
Features.Tools.Wireless Ports=1
Features.Firmware.Version=007.000.011
Features.Firmware.Major Version=007
Features.Firmware.Minor Version=000
Features.Firmware.Build Number=011
Features.Firmware.Available Versions=1: 007.000.011
Features.Firmware.Maximum Versions=1
Features.Firmware.Configuration Check=0
Features.Firmware.Package Number=014.002
Features.Firmware.Combined Firmware Revision=014
Features.Firmware.Available Combined Firmware Revisions=014
Features.Firmware.Safeloader Version=007.000.011
Features.Hardware.Serial Number=P6-00470
Features.Hardware.OEM Number= 
Features.Hardware.Model=Polaris Vicra
Config.Multi Firmware.Load Combined Firmware Revision=0
Config.Multi Firmware.Update Combined Firmware Revision=0
Config.Multi Firmware.Available Combined Firmware Revisions=014
Config.Password=
Config.Combined Firmware Revision=014
Config.Ext Device Syncing=0
Device.Type.0=PS
Device.Instance.0=0
"""

rx_bytes = bytearray()
rx_print_last = None

def parse_rx(rx_bytes):
    if not rx_bytes.endswith(b'\r'):
        raise RuntimeError("Expected \r at end of rx!")

    # Parse command
    command_match = re.match(rb'^[A-Za-z]+[: ]', rx_bytes)
    if command_match is None:
        raise ValueError(f"Error parsing command from '{rx_bytes}'!")
    # match span includes <:>/<space>
    separator_idx = command_match.end()-1
    separator = rx_bytes[separator_idx:separator_idx+1] # get as bytes object
    command = rx_bytes[:separator_idx].decode(encoding="utf-8", errors="strict")
    print(type(separator))

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

def send_reply(str_to_send, append_crc=True, append_cr=True, debug=False):
    tx_bytes = str_to_send.encode()
    if append_crc:
        tx_bytes += calc_crc16_str(tx_bytes).encode()
    if append_cr:
        tx_bytes += "\r".encode()

    ser.write(tx_bytes)
    if debug:
        print(f"Sent: {tx_bytes}")
    
    # clear rx
    rx_bytes.clear()

def reset():
    # clear tx
    ser.flush()
    time.sleep(0.01 * ser.out_waiting)

    # reset to 9600 8N1
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE

    # clear rx
    rx_bytes.clear()
    global rx_print_last
    rx_print_last = None

try:
    while True:
        while ser.in_waiting > 0:
            b = ser.read(1)
            rx_bytes.extend(b)

            # printing
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

        # Serial break
        if rx_bytes == b'\0': # TODO: Will a null byte ever be sent NOT as a serial break?
            print("Received serial break (NULL), resetting...")
            reset()
            send_reply("RESET", debug=True)
            continue

        if rx_bytes.endswith(b'\r'):
            command, args, crc_int = parse_rx(rx_bytes)
            
            if command == "INIT":
                send_reply("OKAY", debug=True)
            elif command == "VER":
                send_reply(VER_STR_CUSTOM, debug=True)
            elif command == "COMM" and args == "60000":
                print(">>> CHANGING BAUD RATE <<<")
                send_reply("OKAY", debug=True)
                time.sleep(0.05) # wait for OKAY reply to finish sending @ 9600 baud rate
                ser.baudrate = 921600
            elif command == "APIREV":
                send_reply(APIREV_STR, debug=True)
            elif command == "GET":
                search_key = rx_bytes[4:-5].decode(encoding="utf-8", errors="strict") #TODO: improve this arg parsing
                matching_attrs = [line for line in GET_ATTRS.split("\n") if re.search(search_key, line.split("=")[0]) is not None]
                if len(matching_attrs) == 0:
                    raise RuntimeError() # TODO: send error back
                send_reply("\n".join(matching_attrs))
            elif command == "SFLIST" and args == "02": # Supported Features List
                send_reply("6", debug=True) # Option 2 -> # wireless tool ports -> 6
            elif command == "TSTART":
                send_reply("OKAY", debug=True)
            elif command == "TSTOP":
                send_reply("OKAY", debug=True)
            elif command == "BX":
                pass
            else:
                raise NotImplementedError(f"Received unrecognized command: '{command}'")
except KeyboardInterrupt:
    pass
