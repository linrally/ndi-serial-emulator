class BaseCommand:
    def __init__(self, ser, err, prt):
        self.ser = ser
        self.err = err
        self.prt = prt
    
    @property
    def name(self):
        raise NotImplementedError("Each command must have a name property")

    def execute(self, args):
        raise NotImplementedError("Each command must implement an execute method")