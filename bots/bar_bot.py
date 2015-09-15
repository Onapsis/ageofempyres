import os
try:
    import time
except:
    pass

import bot_id
    
import time
import os


class BaseBot():

    def __init__(self):
        self._get_turns()
        
    def send_command(self, msg):
        return os.listdir(msg)
    
    def on_turn(self, msg):
        raise NotImplementedError
        
    def _get_turns(self):
        self.on_turn(os.listdir(bot_id.id))


class Mybot(BaseBot):

    def __init__(self):
        BaseBot.__init__(self)
        
    def on_turn(self, msg):
        print "Turn data: ", msg
        self.send_command("sarlanga")
        
a = Mybot()
