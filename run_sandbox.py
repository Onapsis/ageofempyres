#! /usr/bin/env python

import sys
import os

PYPY_PATH = '/home/pguridi/src/pypy-2.6.1-src'
EXECUTABLE = os.path.join(PYPY_PATH, 'pypy/goal/pypy-c')
sys.path.insert(0, os.path.realpath(PYPY_PATH))

from rpython.translator.sandbox.sandlib import SimpleIOSandboxedProc
from rpython.translator.sandbox.sandlib import VirtualizedSandboxedProc


from rpython.translator.sandbox.vfs import Dir, RealDir, RealFile
import pypy
LIB_ROOT = os.path.dirname(os.path.dirname(pypy.__file__))

import uuid
import time
from multiprocessing import Process, Queue, Event
from Queue import Empty

DEBUG = False

def get_cookie():
    return uuid.uuid4().hex[0:8]

def copy_basebot(bot_script, bot_cookie):
    bot_dir = os.path.dirname(bot_script)
    with open("basebot.py", "r") as fr:
        base_content = fr.read()
        base_content = "BOT_COOKIE='"+bot_cookie + "'\n" + base_content
        with open(os.path.join(bot_dir, "basebot.py"), "w+") as fw:
            fw.write(base_content)


class SandboxedBoTController(VirtualizedSandboxedProc, SimpleIOSandboxedProc):
    argv0 = '/bin/pypy-c'
    virtual_cwd = '/tmp'
    virtual_env = {}
    virtual_console_isatty = True

    def __init__(self, bot_cookie, bot_file, bot_queue, turn_event, std_out_queue, stop_event, tmpdir=None):
        self.executable = os.path.abspath(EXECUTABLE)
        self.turn_event = turn_event
        self.stop_event = stop_event
        self.std_out_queue = std_out_queue
        self.registered_event = Event()
        self.first_turn = False
        self.tmpdir = tmpdir
        self._exit = False
        self.debug = DEBUG
        self.queue = bot_queue
        self.bot_cookie = bot_cookie
        self.turn_cookie = None
        self.script_path = os.path.join(self.virtual_cwd, bot_file)
        super(SandboxedBoTController, self).__init__([self.argv0] + [self.script_path],
                                                executable=self.executable)
   
    def logg(self, msg):
        if not self.turn_cookie:
            turn_cookie = str(self.turn_cookie)
        else:
            turn_cookie = self.turn_cookie
        self.std_out_queue.put("[CONTROLLER][%s][%s] %s" % (self.bot_cookie, turn_cookie, str(msg)))

    # def _get_turn(self):
    #     self.turn_cookie = None
    #     if self._exit:
    #         return self.pack_bot_msg("CLOSED")
    #     # should wait for a new turn
    #     # msg is alwasy k,v
    #     self.logg("WAITING FOR TURN")
    #     msg = self.queue.get()
    #     if msg[0] == "QUIT":
    #         self._exit = True
    #         return self.pack_bot_msg(msg[0])
    #     elif msg[0] == "TURN":
    #         self.first_turn = False
    #         # send turn cookie to bot
    #         #self.logg("\nSTARTED TURN")
    #         self.turn_cookie = msg[1]
    #         return self.pack_bot_msg(msg[0])

    def finish_turn(self):
        self.logg("FINISHED TURN")
        self.turn_cookie = None
        self.turn_event.clear()

    def parse_payload(self, data):
        # payload would be like ona#botcookie#turncooki#action#action_arguments
        print "PAYLOAD: ", data
        payload = data.split("#")
        if len(payload[4]) > 1:
            action_args = payload[4].split("%")
        parsed_dict = {'bot_cookie': payload[1],
                       'turn_cookie': payload[2],
                       'action': payload[3],
                       'action_args': action_args}
        return parsed_dict

    def take_action(self, action, args=None):
        print "action: " + action + str(args)
        if action == "LOG":
            self.std_out_queue.put(str(args))
        else:
            # unknown action, looses turn
            self.logg(">>> PLAYER SKIPPED TURN")
            self.finish_turn()
            #self.logg("ACTION-> %s %s" % (str(action), str(action_args)))

    def pack_bot_msg(self, action, args=None):
        return [str(self.turn_cookie), str(action), str(args)]

    def do_ll_os__ll_os_listdir(self, vpathname):
        if "ona" not in vpathname:
            # this is real os.listdir() call
            node = self.get_node(vpathname)
            return node.keys()

        bot_data = self.parse_payload(vpathname)

        # Validate if this is my bot
        if bot_data['bot_cookie'] != self.bot_cookie:
            self.logg("@@@@@@ BAD BOY! - INVALID BOT COOKIE")
            self.finish_turn()
            return ["INVALID BOT COOKIE"]

        if self.stop_event.is_set():
            return self.pack_bot_msg("QUIT")

        # validate if we are in a turn
        if self.turn_event.is_set():
            if bot_data['turn_cookie'] == self.turn_cookie:
                # This is still my turn
                # The bot can take actions here
                self.take_action(bot_data['action'], bot_data['action_args'])
                return self.pack_bot_msg("DONE")
            else:
                # First move of the turn
                # We should have a turn cookie now
                try:
                    self.turn_cookie = self.queue.get_nowait()[1]
                except Empty, e:
                    return self.pack_bot_msg("NOT_YOUR_TURN")
                else:
                    return self.pack_bot_msg("TURN")
        else:
            # we are not in a turn
            return self.pack_bot_msg("NOT_YOUR_TURN")

    def build_virtual_root(self):
        # build a virtual file system:
        # * can access its own executable
        # * can access the pure Python libraries
        # * can access the temporary userssion directory as /tmp
        exclude = ['.pyc', '.pyo']
        tmpdirnode = RealDir(self.tmpdir, exclude=exclude)
        libroot = str(LIB_ROOT)

        return Dir({
            'bin': Dir({
                'pypy-c': RealFile(self.executable, mode=0111),
                'lib-python': RealDir(os.path.join(libroot, 'lib-python'),
                                      exclude=exclude), 
                'lib_pypy': RealDir(os.path.join(libroot, 'lib_pypy'),
                                      exclude=exclude),
                }),
             'tmp': tmpdirnode,
             })


def bot_worker(bot_dict, bot_queue, turn_event, std_out_queue, stop_event):
    bot_dir = os.path.abspath(os.path.dirname(bot_dict["bot_script"]))
    bot_file = os.path.basename(bot_dict["bot_script"])
    sandproc = SandboxedBoTController(bot_dict["bot_cookie"],
                                 bot_file,
                                 bot_queue,
                                 turn_event,
                                 std_out_queue,
                                 stop_event,
                                 tmpdir=bot_dir)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()


def run_match(players):
    std_out_queue = Queue()
    stop_event = Event()
    for bot_id in players.keys():
        players[bot_id]["queue"] = Queue()
        players[bot_id]["turn_event"] = Event()
        # create a bot id
        players[bot_id]["bot_cookie"] = get_cookie()
        copy_basebot(players[bot_id]["bot_script"],
                     players[bot_id]["bot_cookie"])
        
        p = Process(target=bot_worker, args=(players[bot_id],
                                             players[bot_id]["queue"],
                                             players[bot_id]["turn_event"],
                                             std_out_queue,
                                             stop_event
                                             ))
        p.start()

    for i in range(0, 5):
        std_out_queue.put("\n\nStarting round %s\n" % str(i))
        # 10 turns
        for k in players.keys():
            turn_cookie = get_cookie()
            std_out_queue.put("\n===== STARTED TURN %s FOR BOT %s" % (turn_cookie,
                                                                      players[k]["bot_cookie"]))
            players[k]["queue"].put(["TURN", turn_cookie])
            players[k]["turn_event"].set()
            # Wait for the player to finish...
            while players[k]["turn_event"].is_set():
                time.sleep(0.01)
            std_out_queue.put("===== ENDED TURN %s FOR BOT %s" % (turn_cookie,
                                                                      players[k]["bot_cookie"]))
    # Exit
    stop_event.set()

    while not std_out_queue.empty():
        print std_out_queue.get()

if __name__ == '__main__':
    run_match({1: {"bot_script": "bots/bot1/script.py"}, 2: {"bot_script": "bots/bot2/script.py"}})
