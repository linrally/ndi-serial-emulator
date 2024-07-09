class PortHandleManager:
    def __init__(self):
        self.port_handles = {}
    
    def create_handle(self):
        i = 0x01
        while i in self.port_handles:
            i += 1
        self.port_handles[i] = {
            'occupied': False,
            'initialized': False,
            'enabled': False,
            'rom': bytearray(b'\x00' * 1024),  # 1 kB ROM
            'pose': {
                'quaternion' : [1, 0, 0, 0],
                'transform' : [0, 0, 0],
                'rms_error' : 0,
            }
        }
        return i
    
    def initialize_handle(self, handle_id):
        handle = self.port_handles.get(handle_id)
        if handle:
            handle['initialized'] = True
            return True
        return False
    
    def enable_handle(self, handle_id):
        handle = self.port_handles.get(handle_id)
        if handle:
            handle['enabled'] = True
            return True
        return False
    
    def disable_handle(self, handle_id):
        handle = self.port_handles.get(handle_id)
        if handle:
            handle['enabled'] = False
            return True
        return False
    
    def delete_handle(self, handle_id):
        if handle_id in self.port_handles:
            del self.port_handles[handle_id]
            return True
        return False
    
    def write_to_rom(self, handle_id, address, data):
        handle = self.port_handles.get(handle_id)
        if handle:
            handle['rom'][address:address+64] = data  # 64 bytes of data
            handle['occupied'] = True
            return True
        return False
    
    def get_port_status(self, handle): # change to be id
        bits = 0
        if handle.get("occupied"):
            bits |= 1
        if handle.get("initialized"):
            bits |= 1 << 4
        if handle.get("enabled"):
            bits |= 1 << 5
        return bits
    
    def load_transform(self, handle_id, pose):
        handle = self.port_handles.get(handle_id)
        if handle:
            handle['pose'] = pose
            return True
        return False