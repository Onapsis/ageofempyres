import os
try:
    import time
except:
    pass

class BaseBot():

    def __init__(self):
        self._get_turns()

    def send_command(self, msg):
        return os.listdir(msg)

    def on_turn(self, msg):
        raise NotImplementedError

    def _get_turns(self):
        msg = os.listdir(BOT_COOKIE)
        if msg == "QUIT":
            return
        else:
            self.on_turn(msg)
