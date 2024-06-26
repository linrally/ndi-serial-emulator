import time

class FrameManager:
    def __init__(self): pass

    def start(self):
        self.isTracking = False
        self.start_time = time.time()
        self.frame_number = 0
    
    def update(self):
        self.frame_number = int((time.time() - self.start_time) * 60)
