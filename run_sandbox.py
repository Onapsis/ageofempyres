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

    def __init__(self, bot_cookie, bot_file, bot_queue, finished_turn_event, std_out_queue, tmpdir=None):
        self.executable = os.path.abspath(EXECUTABLE)
        self.finished_turn = finished_turn_event
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
        time.sleep(0.2)
        if not self.turn_cookie:
            turn_cookie = str(self.turn_cookie)
        else:
            turn_cookie = self.turn_cookie[0:8]
        self.std_out_queue.put("[CONTROLLER][%s][%s] %s" % (self.bot_cookie[0:5], turn_cookie, str(msg)))

    def _wait_for_turn(self):
        self.turn_cookie = None
        if self._exit:
            return self.pack_bot_msg("CLOSED")
        # should wait for a new turn
        # msg is alwasy k,v
        self.logg("WAITING FOR TURN")
        msg = self.queue.get()
        if msg[0] == "QUIT":
            self._exit = True
            return self.pack_bot_msg(msg[0])
        elif msg[0] == "TURN":
            self.first_turn = False
            # send turn cookie to bot
            #self.logg("\nSTARTED TURN")
            self.turn_cookie = msg[1]
            return self.pack_bot_msg(msg[0])

    def finish_turn(self):
        self.logg("FINISHED TURN")
        self.turn_cookie = None
        self.finished_turn.set()

    def parse_payload(self, data):
        # payload would be like ona#botcookie#turncooki#action#action_arguments
        payload = data.split("#")
        parsed_dict = {'bot_cookie': payload[1],
                       'turn_cookie': payload[2],
                       'action': payload[3],
                       'action_args': payload[4]}
        return parsed_dict

    def take_action(self, action, args=None):
        print "action: " + action + str(args)
        if action == "LOG":
            self.std_out_queue.put(str(args))
            return self.pack_bot_msg("DONE")
        elif action == "REGISTER":
            self.registered_event.set()
            self.first_turn = True
            self.logg("REGISTERED")
            return self.pack_bot_msg("REGISTERED")
        elif action == "WAITING":
            return self._wait_for_turn()
        else:
            # unknown action, looses turn
            self.logg(">>> PLAYER SKIPPED TURN")
            self.finish_turn()
            #self.logg("ACTION-> %s %s" % (str(action), str(action_args)))

    def pack_bot_msg(self, action, args=None):
        return [str(self.turn_cookie), str(action), str(args)]

    def do_ll_os__ll_os_listdir(self, vpathname):
        print "GOT: ", vpathname
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

        # validate if we are in a turn
        if not self.turn_cookie:
            # we are not in turn, check for first call
            if not self.registered_event.is_set():
                # bot is not registered, this is first call
                return self.take_action("REGISTER")
            if self.first_turn:
                # this is the first turn
                return self._wait_for_turn()
            else:
                # Bot already registered, but not in turn
                self.logg("@@@@@@ BAD BOY! - NOT IN TURN")
                return self.pack_bot_msg("ERROR")

        if bot_data['turn_cookie'] == self.turn_cookie:
            # This is my turn
            # The bot can take actions here
            self.take_action(bot_data['action'], bot_data['action_args'])
            return self.pack_bot_msg("DONE")
        else:
            # this bot might be bruteforcing the turns.
            self.logg("@@@@@@ BAD BOY! - WRONG TURN COOKIE")
            self.finish_turn()
            #return self._wait_for_turn()

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


def bot_worker(bot_dict, bot_queue, turn_event, std_out_queue):
    bot_dir = os.path.abspath(os.path.dirname(bot_dict["bot_script"]))
    bot_file = os.path.basename(bot_dict["bot_script"])
    sandproc = SandboxedBoTController(bot_dict["bot_cookie"],
                                 bot_file,
                                 bot_queue,
                                 turn_event,
                                 std_out_queue,
                                 tmpdir=bot_dir)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()


def run_match(players):
    std_out_queue = Queue()
    for bot_id in players.keys():
        players[bot_id]["queue"] = Queue()
        players[bot_id]["finished_turn_event"] = Event()
        # create a bot id
        players[bot_id]["bot_cookie"] = get_cookie()
        copy_basebot(players[bot_id]["bot_script"],
                     players[bot_id]["bot_cookie"])
        
        p = Process(target=bot_worker, args=(players[bot_id],
                                             players[bot_id]["queue"],
                                             players[bot_id]["finished_turn_event"],
                                             std_out_queue
                                             ))
        p.start()

    for i in range(0, 5):
        std_out_queue.put("\n\nStarting round %s\n" % str(i))
        # 10 turns
        for k in players.keys():
            turn_cookie = get_cookie()
            std_out_queue.put("\n===== STARTED TURN %s FOR BOT %s" % (turn_cookie[0:8],
                                                                      players[k]["bot_cookie"][0:5]))
            players[k]["finished_turn_event"].clear()
            players[k]["queue"].put(["TURN", turn_cookie])
            players[k]["finished_turn_event"].wait()
            std_out_queue.put("===== ENDED TURN %s FOR BOT %s" % (turn_cookie[0:8],
                                                                      players[k]["bot_cookie"][0:5]))

    # Exit
    for k in players.keys():
        players[k]["queue"].put(["QUIT"])

    while not std_out_queue.empty():
        print std_out_queue.get()

if __name__ == '__main__':
    run_match({1: {"bot_script": "bots/bot1/script.py"}, 2: {"bot_script": "bots/bot2/script.py"}})
