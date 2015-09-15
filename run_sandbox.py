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

import sys, os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..')))
from rpython.translator.sandbox.sandlib import SimpleIOSandboxedProc
from rpython.translator.sandbox.sandlib import VirtualizedSandboxedProc
from rpython.translator.sandbox.sandlib import VirtualizedSocketProc
from rpython.translator.sandbox.vfs import Dir, RealDir, RealFile
import pypy
LIB_ROOT = os.path.dirname(os.path.dirname(pypy.__file__))

import uuid
import shutil
import time
from multiprocessing import Process, Queue

TMP_DIR = "sandbox_tmps"
EXECUTABLE = '../goal/pypy-c'


def get_cookie():
    return uuid.uuid4().hex


class BotHandler(object):

    def __init__(self, path):
        self.bot_id = uuid.uuid4().hex
        self.queue = Queue()
        self.path = path
        fdir, fname = os.path.split(path)
        self.fname = fname
        self.sandbox_dir = None

    def create_sandbox_dir(self):
        self.sandbox_dir = os.path.join(TMP_DIR, self.bot_id)
        os.mkdir(self.sandbox_dir)
        shutil.copy(self.path, os.path.join(self.sandbox_dir, "bot.py"))
        with open(os.path.join(self.sandbox_dir, "bot_id.py"), "w+") as f:
            f.write("id='"+self.bot_id+"'")
        

class PyPySandboxedProc(VirtualizedSandboxedProc, SimpleIOSandboxedProc):
    argv0 = '/bin/pypy-c'
    virtual_cwd = '/tmp'
    virtual_env = {}
    virtual_console_isatty = True
    

    def __init__(self, executable, bot_id, arguments, tmpdir=None, debug=True):
        self.executable = executable = os.path.abspath(executable)
        self.tmpdir = tmpdir
        self.debug = debug
        self.bot_id = bot_id
        super(PyPySandboxedProc, self).__init__([self.argv0] + arguments,
                                                executable=executable)
   
    def do_ll_os__ll_os_getcwd(self):
        # got turn!
        turn_cookie = get_cookie()
        time.sleep(5)
        return turn_cookie
        
    def do_ll_os__ll_os_listdir(self, bot_id):
        if bot_id != self.bot_id:
            print "INVALID COOKIE!", bot_id
        else:
            print "GOT REQUEST FROM BOT: ", bot_id
        return []
        
    #def do_ll_os__ll_os_getenv(self, bot_id):
    #    # Registered bot!
    #    print "GOT BOT ID: ", bot_id
    #    return "sarasa"
    
    def build_virtual_root(self):
        # build a virtual file system:
        # * can access its own executable
        # * can access the pure Python libraries
        # * can access the temporary usession directory as /tmp
        exclude = ['.pyc', '.pyo']
        if self.tmpdir is None:
            tmpdirnode = Dir({})
        else:
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


def bot_worker(bot_id, bot_dir, turns_queue, extraoptions, debug, timeout, logfile):
    sandproc = PyPySandboxedProc(EXECUTABLE, bot_id, extraoptions + ["/tmp/bot.py"],
                                    tmpdir=bot_dir, debug=debug)
    if timeout is not None:
        sandproc.settimeout(timeout, interrupt_main=True)
    if logfile is not None:
        sandproc.setlogfile(logfile)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()


def main():
    from getopt import getopt      # and not gnu_getopt!
    options, arguments = getopt(sys.argv[1:], 't:hv', 
                                ['tmp=', 'heapsize=', 'timeout=', 'log=',
                                 'verbose', 'help'])
    executable = '../goal/pypy-c'
    timeout = None
    logfile = None
    debug = False
    extraoptions = []

    def help():
        print >> sys.stderr, __doc__
        sys.exit(2)

    for option, value in options:
        if option == '--heapsize':
            value = value.lower()
            if value.endswith('k'):
                bytes = int(value[:-1]) * 1024
            elif value.endswith('m'):
                bytes = int(value[:-1]) * 1024 * 1024
            elif value.endswith('g'):
                bytes = int(value[:-1]) * 1024 * 1024 * 1024
            else:
                bytes = int(value)
            if bytes <= 0:
                raise ValueError
            if bytes > sys.maxint:
                raise OverflowError("--heapsize maximum is %d" % sys.maxint)
            extraoptions[:0] = ['--heapsize', str(bytes)]
        elif option == '--timeout':
            timeout = int(value)
        elif option == '--log':
            logfile = value
        elif option in ['-v', '--verbose']:
            debug = True
        elif option in ['-h', '--help']:
            help()
        else:
            raise ValueError(option)

    if len(arguments) < 1:
        help()
    
    bots = []
    for bot_script in arguments[0:]:
        bot = BotHandler(bot_script)
        bots.append(bot)
        # create bot sandbox dir and copy it inside
        bot.create_sandbox_dir()
        
        p = Process(target=bot_worker, args=(bot.bot_id, bot.sandbox_dir, 
            bot.queue, extraoptions, debug, timeout, logfile))
        p.start()
        

if __name__ == '__main__':
    main()
