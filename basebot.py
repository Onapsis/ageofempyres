import os
try:
    import time
except:
    pass


class BaseBot(object):

    def __init__(self):
        self._exit = False
        self._turn_cookie = None
        self._actions = []
        self._get_turns()

    def pack_msg(self, action, args=None):
        data = "ona#"+"#".join([BOT_COOKIE, str(self._turn_cookie), str(action), str(args)])
        return data

    def log(self, msg):
        #os.listdir(self.pack_msg("LOG", msg))
        print "\n[BOT][%s]" % BOT_COOKIE, msg

    def on_turn(self, msg):
        raise NotImplementedError

    def attack(self, victim):
        self._actions.append(self.pack_msg("ATTACK", victim))

    def _get_turns(self):
        if self._exit:
            return
        msg = os.listdir(self.pack_msg("WAITING"))
        self._turn_cookie = msg[0]
        self.log(msg)
        if msg[1] == "QUIT":
            self._exit = True
            return
        elif msg[1] == "REGISTERED":
            self._get_turns()
        elif msg[1] == "TURN":
            self.on_turn(msg)
            msg = os.listdir(self.pack_msg("ACTION", self._actions))
            # check msg for exceptions
            self._get_turns()
        else:
            print "NOTHING TO DO", msg