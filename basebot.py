import os
try:
    import time
except:
    pass

import time


class BaseBot(object):

    def __init__(self):
        self._exit = False
        self._turn_cookie = None
        self._actions = []
        self._get_turns()

    def pack_msg(self, action, args=None):
        data = "ona#"+"#".join([BOT_COOKIE, str(self._turn_cookie), str(action), str(args)])
        return data

    def unpack_msg(self, msg):
        return {'turn_cookie': str(msg[0]),
                'msg': str(msg[1]),
                'args': str(msg[2])}

    def log(self, msg):
        os.listdir(self.pack_msg("LOG", msg))
        #print "\n[BOT][%s]" % BOT_COOKIE, msg

    def on_turn(self, msg):
        raise NotImplementedError

    def attack(self, victim):
        self._actions.append('%'.join(["ATTACK", victim]))

    def _get_turns(self):
        while True:
            time.sleep(0.2)
            ret = self.unpack_msg(os.listdir(self.pack_msg("IS_MY_TURN")))
            self.log(ret)

            if ret['msg'] == "QUIT":
                self._exit = True
                return

            if ret['msg'] == 'TURN':
                self._turn_cookie = ret['turn_cookie']
                self.on_turn(ret)
                ret = self.unpack_msg(os.listdir(self.pack_msg("ACTION", ','.join(self._actions))))
                # check msg for exceptions
            else:
                continue