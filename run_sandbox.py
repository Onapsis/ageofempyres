#! /usr/bin/env python

"""Interacts with a PyPy subprocess translated with --sandbox.

Usage:
    pypy_interact.py [options] <executable> <args...>

Options:
    --tmp=DIR     the real directory that corresponds to the virtual /tmp,
                  which is the virtual current dir (always read-only for now)
    --heapsize=N  limit memory usage to N bytes, or kilo- mega- giga-bytes
                  with the 'k', 'm' or 'g' suffix respectively.
    --timeout=N   limit execution time to N (real-time) seconds.
    --log=FILE    log all user input into the FILE.
    --verbose     log all proxied system calls.

Note that you can get readline-like behavior with a tool like 'ledit',
provided you use enough -u options:

    ledit python -u pypy_interact.py pypy-c-sandbox -u
"""
import sys
import os

PYPY_PATH = '/home/pguridi/src/pypy-2.6.1-src'
EXECUTABLE = os.path.join(PYPY_PATH, 'pypy/goal/pypy-c')
sys.path.insert(0, os.path.realpath(PYPY_PATH))

from rpython.translator.sandbox.sandlib import SimpleIOSandboxedProc
from rpython.translator.sandbox.sandlib import VirtualizedSandboxedProc
#from rpython.translator.sandbox.sandlib import VirtualizedSocketProc
from rpython.translator.sandbox.vfs import Dir, RealDir, RealFile
import pypy
LIB_ROOT = os.path.dirname(os.path.dirname(pypy.__file__))

import uuid
import time
from multiprocessing import Process, Queue

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


# def create_sandbox_dir(bot_script, bot_cookie):
#     sandbox_dir = os.path.join(TMP_DIR, bot_cookie)
#     if not os.path.exists(sandbox_dir):
#         os.mkdir(sandbox_dir)
#
#     with open(bot_script, "r") as f:
#         bot_content = f.read()
#         bot_content = "BOT_COOKIE='"+bot_cookie + "\n" + bot_content
#         with open(os.path.join(sandbox_dir, "bot.py"), "w+") as f:
#             f.write(bot_content)
#
#     return sandbox_dir
#     #shutil.copy(bot_script, os.path.join(sandbox_dir, "bot.py"))


# class BotHandler(object):
#
#     def __init__(self, path):
#         self.bot_id = uuid.uuid4().hex
#         self.queue = Queue()
#         self.path = path
#         fdir, fname = os.path.split(path)
#         self.fname = fname
#         self.sandbox_dir = None
#
#     def create_sandbox_dir(self):
#         self.sandbox_dir = os.path.join(TMP_DIR, self.bot_id)
#         os.mkdir(self.sandbox_dir)
#         shutil.copy(self.path, os.path.join(self.sandbox_dir, "bot.py"))
#         with open(os.path.join(self.sandbox_dir, "bot_id.py"), "w+") as f:
#             f.write("id='"+self.bot_id+"'")
        

class PyPySandboxedProc(VirtualizedSandboxedProc, SimpleIOSandboxedProc):
    argv0 = '/bin/pypy-c'
    virtual_cwd = '/tmp'
    virtual_env = {}
    virtual_console_isatty = True

    def __init__(self, bot_cookie, bot_file, bot_queue, tmpdir=None):
        self.executable = os.path.abspath(EXECUTABLE)
        self.tmpdir = tmpdir
        self.debug = DEBUG
        self.queue = bot_queue
        self.bot_cookie = bot_cookie
        self.script_path = os.path.join(self.virtual_cwd, bot_file)
        super(PyPySandboxedProc, self).__init__([self.argv0] + [self.script_path],
                                                executable=self.executable)
   
    # def do_ll_os__ll_os_getcwd(self):
    #     # got turn!
    #     turn_cookie = get_cookie()
    #     time.sleep(1)
    #     return turn_cookie

    def do_ll_os__ll_os_listdir(self, bot_id):
        msg = self.queue.get()
        print "MSG: ", msg
        if msg == "QUIT":
            return ["QUIT"]

        if bot_id != self.bot_cookie:
            print "INVALID COOKIE!", bot_id
        else:
            print "GOT REQUEST FROM BOT: ", bot_id
        return []

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


def bot_worker(bot_dict, bot_queue):
    bot_dir = os.path.abspath(os.path.dirname(bot_dict["bot_script"]))
    bot_file = os.path.basename(bot_dict["bot_script"])
    sandproc = PyPySandboxedProc(bot_dict["bot_cookie"],
                                 bot_file,
                                 bot_queue,
                                 tmpdir=bot_dir)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()


def run_match(players):
    for bot_id in players.keys():
        players[bot_id]["queue"] = Queue()
        # create a bot id
        players[bot_id]["bot_cookie"] = get_cookie()
        copy_basebot(players[bot_id]["bot_script"],
                     players[bot_id]["bot_cookie"])
        
        p = Process(target=bot_worker, args=(players[bot_id],
                                             players[bot_id]["queue"],
                                             ))
        p.start()

    print "Sending close.."
    for k in players.keys():
        players[k]["queue"].put("QUIT")

    time.sleep(1)

if __name__ == '__main__':
    run_match({1: {"bot_script": "bots/bot1/script.py"}, 2: {"bot_script": "bots/bot2/script.py"}})
