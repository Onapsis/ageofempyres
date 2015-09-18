from basebot import BaseBot


class Mybot(BaseBot):

    def __init__(self):
        BaseBot.__init__(self)
        
    def on_turn(self, msg):
        self.attack("russia")
        
a = Mybot()
