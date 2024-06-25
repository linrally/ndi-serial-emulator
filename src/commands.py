from base_command import BaseCommand

class RESETCommand(BaseCommand):
    @property
    def name(self):
        return "RESET"
    
    def execute(self, args):
        self.ser.reset()
        self.ser.send_reply("RESET", debug=True)
        return 0