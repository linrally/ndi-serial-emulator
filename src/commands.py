from base_command import BaseCommand
from crc import CRC
from config import *
import time
import serial
import re
import struct

class RESETCommand(BaseCommand):
    name = "RESET"

    def execute(self, args):
        self.ser.reset()
        self.ser.send_reply("RESET", debug=True)
        return 0

class INITCommand(BaseCommand):
    name = "INIT"
    
    def execute(self, args):
        self.ser.send_reply("OKAY", debug=True)
        return 0
    
class VERCommand(BaseCommand):
    name = "VER"

    def execute(self, args):
        self.ser.send_reply(VER_STR_CUSTOM, debug=True)
        return 0

class COMMCommand(BaseCommand):
    name = "COMM"

    def execute(self, args):
        CONVERT_BAUD = [9600, 14400, 19200, 38400, 57600, 115200, 921600, 1228739]
        newspeed = 9600
        newdps = "8N1"
        newhand = 0 # Handshaking parsed, but not implemented

        self.ser.send_reply("OKAY", debug=True) # TODO: Error should be returned before the baud change
        time.sleep(0.05) # Delay to allow buffer to clear before changing baud rate

        if (args[0] >= '0' and args[0] <= '7') or args[0] == 'A':
            if args[0] != 'A':
                newspeed = CONVERT_BAUD[int(args[0])]
            else:
                newspeed = 230400
        if args[1] == '1':
            newdps[0] = '7'
        if args[2] == '1':
            newdps[1] = 'O'
        elif args[2] == '2':
            newdps[1] = 'E'
        if args[3] == '1':
            newdps[2] = '2'
        if args[4] == '1':
            newhand = 1
    
        try:
            self.ser.ser.baudrate = newspeed
        
            if newdps[1] == "N":
                self.ser.ser.parity = serial.PARITY_NONE
            elif newdps[1] == "O":
                self.ser.ser.parity = serial.PARITY_ODD
            elif newdps[1] == "E":
                self.ser.ser.parity = serial.PARITY_EVEN
        
            if newdps[0] == '7':
                self.ser.ser.bytesize = serial.SEVENBITS
            elif newdps[0] == '8':
                self.ser.ser.bytesize = serial.EIGHTBITS

            if newdps[2] == '1':
                self.ser.ser.stopbits = serial.STOPBITS_ONE
            elif newdps[2] == '2':
                self.ser.ser.stopbits = serial.STOPBITS_TWO

            return 0
        except:
            self.err.set_error(NDI_BAD_COMM)
            return -1
        
class APIREVCommand(BaseCommand):
    name = "APIREV"

    def execute(self, args):
        self.ser.send_reply(APIREV_STR, debug=True)
        return 0

class GETCommand(BaseCommand):
    name = "GET"

    def execute(self, args):
        matching_attrs = [line for line in GET_ATTRS.split("\n") if re.search(args, line.split("=")[0]) is not None]
        if len(matching_attrs) == 0:
            self.err.set_error(NDI_NO_USER_PARAM)
            return -1
        self.ser.send_reply("\n".join(matching_attrs), debug=True)
        return 0

class SFLISTCommand(BaseCommand):
    name = "SFLIST"

    def execute(self, args):
        reply_option = int(args[0:2], 16)
        if reply_option == 0x02:
            self.ser.send_reply("6", debug=True)
        return 0

class TSTARTCommand(BaseCommand):
    name = "TSTART"

    def execute(self, args):
        # TODO: implement alt reply option
        self.frm.isTracking = True
        self.ser.send_reply("OKAY", debug=True)
        return 0

class TSTOPCommand(BaseCommand):
    name = "TSTOP"

    def execute(self, args):
        self.frm.isTracking = True
        self.ser.send_reply("OKAY", debug=True)
        return 0

class BXCommand(BaseCommand): 
    name = "BX"

    def execute(self, args): 
        reply_option = int(args[0:4], 16) if len(args) >= 7 else NDI_XFORMS_AND_STATUS
        # Check for isTracking and throw error

        body_bytes = bytearray()
        body_bytes.extend(struct.pack("<B", len(self.prt.port_handles)))
        
        for key, value in self.prt.port_handles.items(): # rename key/value    
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
                reply_option_bytes.extend(struct.pack("<I", self.prt.get_port_status(value)))
                reply_option_bytes.extend(struct.pack("<I", self.frm.frame_number))

            body_bytes.extend(reply_option_bytes)

        body_bytes.extend(struct.pack("<H", 0)) # system status 

        header_bytes = bytearray.fromhex("C4A5")
        header_bytes.extend(struct.pack("<H", len(body_bytes))) # reply length

        reply = header_bytes + struct.pack("<H", CRC.calc_crc16_int(header_bytes)) + body_bytes + struct.pack("<H", CRC.calc_crc16_int(body_bytes))
        self.ser.send_reply(reply, debug=True, append_crc=False, append_cr=False, binary=True)

        return 0

class PHRQCommand(BaseCommand):
    name = "PHRQ"

    def execute(self, args):
        device = args[0:8]
        system_type = args[8]
        tool_type = args[9]
        port_number = args[10:12]
        reserved =args[12:14]

        port_handle = self.prt.create_handle()
        self.ser.send_reply(f"{port_handle:02X}", debug=True)

        return 0

class PHSRCommand(BaseCommand):
    name = "PHSR"

    def execute(self, args):
        reply_option = int(args[0:2], 16)

        filtered_handles = {}
        if reply_option == NDI_UNINITIALIZED_HANDLES:
            filtered_handles = {
                key: value 
                for key, value in self.prt.port_handles.items() 
                if value.get("occupied") and not (value.get("initialized") or value.get("enabled"))
            }
        elif reply_option == NDI_UNENABLED_HANDLES:
            filtered_handles = {
                key: value 
                for key, value in self.prt.port_handles.items() 
                if value.get("occupied") and value.get("initialized") and not value.get("enabled")
            }
        elif reply_option == NDI_ENABLED_HANDLES:
            filtered_handles = {
                key: value 
                for key, value in self.prt.port_handles.items() 
                if value.get("enabled")
            }
            
        reply = f"{len(filtered_handles):02X}"
        for key, value in filtered_handles.items():
            reply += f"{key:02X}{self.prt.get_port_status(value):03X}"

        self.ser.send_reply(reply, debug=True)

        return 0
    
class PVWRCommand(BaseCommand):
    name = "PVWR"

    def execute(self, args):
        port_handle = int(args[0:2], 16)
        address = int(args[2:6], 16)
        data = bytearray.fromhex(args[6:6+128])
        self.prt.write_to_rom(port_handle, address, data)
        self.ser.send_reply("OKAY", debug=True)
        return 0
    
class PINITCommand(BaseCommand):
    name = "PINIT"

    def execute(self, args):
        port_handle = int(args[0:2], 16)
        self.prt.initialize_handle(port_handle)
        self.ser.send_reply("OKAY", debug=True)
        return 0

class PENACommand(BaseCommand):
    name = "PENA"

    def execute(self, args):
        port_handle = int(args[0:2], 16)
        tracking_priority = args[2]
        self.prt.enable_handle(port_handle)
        self.ser.send_reply("OKAY", debug=True)
        return 0
    
class PDISCommand(BaseCommand):
    name = "PDIS"

    def execute(self, args):
        port_handle = int(args[0:2], 16)
        self.prt.disable_handle(port_handle)
        self.ser.send_reply("OKAY", debug=True)
        return 0

class PHFCommand(BaseCommand):
    name = "PHF"

    def execute(self, args):
        port_handle = int(args[0:2], 16)
        self.prt.delete_handle(port_handle)
        self.ser.send_reply("OKAY", debug=True)
        return 0
    
COMMANDS_LIST = [
                RESETCommand, 
                INITCommand,
                VERCommand,
                COMMCommand,
                APIREVCommand,
                GETCommand,
                SFLISTCommand,
                TSTARTCommand,
                TSTOPCommand,
                BXCommand,
                PHRQCommand,
                PHSRCommand,
                PVWRCommand,
                PINITCommand,
                PENACommand,
                PDISCommand,
                PHFCommand,
                ]