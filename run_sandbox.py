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
    return uuid.uuid4().hex

def copy_basebot(bot_script, bot_cookie):
    bot_dir = os.path.dirname(bot_script)
    with open("basebot.py", "r") as fr:
        base_content = fr.read()
        base_content = "BOT_COOKIE='"+bot_cookie + "'\n" + base_content
        with open(os.path.join(bot_dir, "basebot.py"), "w+") as fw:
            fw.write(base_content)


class SandboxedBoxController(VirtualizedSandboxedProc, SimpleIOSandboxedProc):
    argv0 = '/bin/pypy-c'
    virtual_cwd = '/tmp'
    virtual_env = {}
    virtual_console_isatty = True

    def __init__(self, bot_cookie, bot_file, bot_queue, turn_event, tmpdir=None):
        self.executable = os.path.abspath(EXECUTABLE)
        self.on_turn = turn_event
        self.tmpdir = tmpdir
        self._exit = False
        self.debug = DEBUG
        self.queue = bot_queue
        self.bot_cookie = bot_cookie
        self.turn_cookie = None
        self.script_path = os.path.join(self.virtual_cwd, bot_file)
        super(SandboxedBoxController, self).__init__([self.argv0] + [self.script_path],
                                                executable=self.executable)
   
    def logg(self, msg):
        print "[CONTROLLER][%s]" % self.bot_cookie[0:5], msg

    def do_ll_os__ll_os_getenv(self, name):
        return self.virtual_env.get(name)

    def _wait_for_turn(self):
        if self._exit:
            return ["CLOSED"]
        # should wait for a new turn
        # msg is alwasy k,v
        self.logg("WAITING FOR TURN")
        msg = self.queue.get()
        if msg[0] == "QUIT":
            self.turn_cookie = None
            self._exit = True
            return [msg[0]]
        elif msg[0] == "TURN":
            # send turn cookie to bot
            return [msg[0], msg[1]]

    def finish_turn(self):
        self.turn_cookie = None
        self.on_turn.clear()

    def do_ll_os__ll_os_listdir(self, data):
        self.logg(data)
        payload = data.split("#")
        bot_cookie, turn_cookie = payload[0], payload[1]
        action, action_args = None, None
        if len(payload) == 4:
            action, action_args = payload[2], payload[3]

        if bot_cookie != self.bot_cookie:
            self.logg("INVALID BOT COOKIE")
            self.finish_turn()
            return ["INVALID BOT COOKIE"]

        self.logg("TURNCOOOOKIE: " + turn_cookie)
        if not self.turn_cookie:
            return self._wait_for_turn()

        if turn_cookie == self.turn_cookie:
            # might take actions here
            self.logg("ACTION->" + action + action_args)
            self.finish_turn()
            return ["DONE"]
        else:
            return self._wait_for_turn()

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


def bot_worker(bot_dict, bot_queue, turn_event):
    bot_dir = os.path.abspath(os.path.dirname(bot_dict["bot_script"]))
    bot_file = os.path.basename(bot_dict["bot_script"])
    sandproc = SandboxedBoxController(bot_dict["bot_cookie"],
                                 bot_file,
                                 bot_queue,
                                 turn_event,
                                 tmpdir=bot_dir)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()


def run_match(players):
    for bot_id in players.keys():
        players[bot_id]["queue"] = Queue()
        players[bot_id]["turn_event"] = Event()
        # create a bot id
        players[bot_id]["bot_cookie"] = get_cookie()
        copy_basebot(players[bot_id]["bot_script"],
                     players[bot_id]["bot_cookie"])
        
        p = Process(target=bot_worker, args=(players[bot_id],
                                             players[bot_id]["queue"],
                                             players[bot_id]["turn_event"]
                                             ))
        p.start()

    for i in range(0, 50):
        print "Round ", i
        # 10 turns
        for k in players.keys():
            players[k]["turn_event"].set()
            turn_cookie = get_cookie()
            players[k]["queue"].put(["TURN", turn_cookie])
            players[k]["turn_event"].wait()

    time.sleep(1)
    # Exit
    for k in players.keys():
        players[k]["queue"].put(["QUIT"])


if __name__ == '__main__':
    run_match({1: {"bot_script": "bots/bot1/script.py"}, 2: {"bot_script": "bots/bot2/script.py"}})
