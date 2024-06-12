import serial

ndi = serial.Serial("/dev/cu.usbserial-110", baudrate=9600, bytesize=8, parity="N", stopbits=1, dsrdtr=False)

ndi.send_break()

rx_bytes = bytearray()
rx_msg = bytearray()
rx_printed_last = None

sent_init = False
asked_version = False
changed_rate = False
sent_echo = False

def calc_crc16(data):
	crc = 0x0000
	for i in (range(0, len(data))):
		crc ^= data[i]
		for k in range(0, 8):
			crc = (crc >> 1) ^ 0xa001 if crc & 1 else crc >> 1
	return crc

def append_crc16(strdata):
	return (strdata + calc_crc16(strdata.encode()).to_bytes(2).hex().upper() + "\r")

ndi.send_break()
assert ndi.read_until("\r".encode()) == "RESETBE6F\r".encode()

ndi.write(append_crc16("INIT:").encode())
assert ndi.read_until("\r".encode()) == "OKAYA896\r".encode()

ndi.write(append_crc16("VER:4").encode())
print("VER: ", ndi.read_until("\r".encode()))

ndi.write(append_crc16("COMM:60000").encode())
assert ndi.read_until("\r".encode()) == "OKAYA896\r".encode()
ndi.baudrate = 921600

def test_cmd(cmdstr):
	ndi.write(append_crc16(f"{cmdstr}").encode())
	print(f"{cmdstr}: ", ndi.read_until("\r".encode()))

test_cmd("SFLIST:02")
