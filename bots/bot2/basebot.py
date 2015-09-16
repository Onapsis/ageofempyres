BOT_COOKIE='ce2b9bbfbb1b491ea344ffad5aa6606b'
import os
try:
    import time
except:
    pass


class BaseBot(object):

    def __init__(self):
        self._exit = False
        self._turn_cookie = "-1"
        self._get_turns()

    def log(self, msg):
        print "[BOT][%s]" % BOT_COOKIE[0:5], msg

    def on_turn(self, msg):
        raise NotImplementedError

    def attack(self, victim):
        return os.listdir("#".join([BOT_COOKIE, self._turn_cookie, "ATTACK", victim]))

    def _get_turns(self):
        if self._exit:
            return
        msg = os.listdir("#".join([BOT_COOKIE, self._turn_cookie]))
        self.log(msg)
        if msg[0] == "QUIT":
            self._turn_cookie = "-1"
            self._exit = True
            return
        elif msg[0] == "TURN":
            self._turn_cookie = msg[1]
            self.on_turn(msg)
            self._get_turns()