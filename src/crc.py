class CRC:
    @staticmethod
    def calc_crc16_int(byte_data): 
        # Translated from C code at https://stackoverflow.com/a/68095008
        crc = 0x0000
        for i in (range(0, len(byte_data))):
            crc ^= byte_data[i]
            for k in range(0, 8):
                crc = (crc >> 1) ^ 0xa001 if crc & 1 else crc >> 1
        return crc
    
    @staticmethod
    def calc_crc16_str(data):
        if isinstance(data, bytes) or isinstance(data, bytearray):
            byte_data = data
        elif isinstance(data, str):
            byte_data = data.encode("utf-8", errors="strict")
        else:
            raise TypeError("Expected data argument to be of type bytes, bytearray, or str")
        return CRC.calc_crc16_int(byte_data).to_bytes(2, byteorder="big").hex().upper()