class ErrorManager:
    def __init__(self):
        self.ErrorCode = 0
    
    def set_error(self, errnum):
        self.ErrorCode = errnum