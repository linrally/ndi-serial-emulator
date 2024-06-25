class BaseCommand:
    name = None

    def __init__(self, ser, err, prt, frm):
        self.ser = ser
        self.err = err
        self.prt = prt
        self.frm = frm
    
    @property
    def name(self):
        raise NotImplementedError("Each command must have a name property")

    def execute(self, args):
        raise NotImplementedError("Each command must implement an execute method")