#! /usr/bin/env python

import sys
import os

PYPY_PATH = '/home/pguridi/src/pypy-2.6.1-src'
EXECUTABLE = os.path.join(PYPY_PATH, 'pypy/goal/pypy-c')
sys.path.insert(0, os.path.realpath(PYPY_PATH))

from rpython.translator.sandbox.sandlib import SimpleIOSandboxedProc
from rpython.translator.sandbox.sandlib import VirtualizedSocketProc


from rpython.translator.sandbox.vfs import Dir, RealDir, RealFile
import pypy
LIB_ROOT = os.path.dirname(os.path.dirname(pypy.__file__))

import uuid
import time
from multiprocessing import Process, Queue, Event
import threading
from Queue import Empty
import SocketServer
import socket

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

HOST, PORT = "localhost", 9999

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        #self.server.bot_controller.handle_request(self.request, self.data)
        #self.request.sendall(self.data.upper())


class SandboxedBoTController(VirtualizedSocketProc, SimpleIOSandboxedProc):
    argv0 = '/bin/pypy-c'
    virtual_cwd = '/tmp'
    virtual_env = {}
    virtual_console_isatty = True

    def __init__(self, bot_cookie, bot_file, bot_queue, turn_event, turn_done_event, std_out_queue, stop_event, port, tmpdir=None):
        self.executable = os.path.abspath(EXECUTABLE)
        self.turn_event = turn_event
        self.turn_done_event = turn_done_event
        self.stop_event = stop_event
        self.std_out_queue = std_out_queue
        self.first_turn = False
        self._server = None
        self._server_thread = None
        self.tmpdir = tmpdir
        self._exit = False
        self.debug = DEBUG
        self.queue = bot_queue
        self.bot_cookie = bot_cookie
        self.turn_cookie = None
        self._fd = None
        self.sock = None
        self.port = port
        self._start_server(port)
        self.start_main_loop()

        self.script_path = os.path.join(self.virtual_cwd, bot_file)
        super(SandboxedBoTController, self).__init__([self.argv0] + [self.script_path],
                                                executable=self.executable)

    def _start_server(self, port):
        # Create the server, binding to localhost
        self._server = SocketServer.TCPServer((HOST, port), MyTCPHandler)
        self._server.bot_controller = self
        print "Starting socket server.."
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()
        print "Server loop running in thread:", self._server_thread.name, " PORT: ", port

    def logg(self, msg):
        if not self.turn_cookie:
            turn_cookie = str(self.turn_cookie)
        else:
            turn_cookie = self.turn_cookie
        self.std_out_queue.put("[CONTROLLER][%s][%s] %s" % (self.bot_cookie, turn_cookie, str(msg)))

    def finish_turn(self):
        self.logg("FINISHED TURN")
        self.turn_cookie = None
        self.turn_event.clear()
        self.turn_done_event.set()

    def unpack(self, data):
        # payload would be like ona#botcookie#turncooki#action#action_arguments
        #print "DATA: ", data
        payload = data.split("#")
        if len(payload[4]) > 1:
            action_args = payload[4].split("$")
        parsed_dict = {'bot_cookie': payload[1],
                       'turn_cookie': payload[2],
                       'action': payload[3],
                       'action_args': action_args}
        #print "DICT: ", parsed_dict
        return parsed_dict

    def take_action(self, action, args=None):
        #print "action: " + action + str(args)
        if action == "LOG":
            self.std_out_queue.put(str(args))
        elif action == "MOVES":
            for move in args:
                #command = move.split('$')
                self.logg("PERFORMING %s" % str(move))
        else:
            # unknown action, looses turn
            self.logg(">>> PLAYER SKIPPED TURN")
            self.finish_turn()
            #self.logg("ACTION-> %s %s" % (str(action), str(action_args)))

    def pack_bot_msg(self, action, args=None):
        return "#".join([str(self.turn_cookie), str(action), str(args)])

    def do_ll_os__ll_os_open(self, name, flags, mode):
        if name.startswith("tcp://"):
            return None
        if not name.startswith("ona://"):
            return super(VirtualizedSocketProc, self).do_ll_os__ll_os_open(
                name, flags, mode)
        import socket
        host, port = "localhost", self.port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, int(port)))
        fd = self.allocate_fd(self.sock)
        self.sockets[fd] = True
        self._fd = fd
        return fd

    def do_ll_os__ll_os_read(self, fd, size):
        if fd in self.sockets:
            return self.get_file(fd).recv(size)
        return super(VirtualizedSocketProc, self).do_ll_os__ll_os_read(
            fd, size)

    def do_ll_os__ll_os_write(self, fd, data):
        if fd in self.sockets:
            return self.get_file(fd).send(data)
        return super(VirtualizedSocketProc, self).do_ll_os__ll_os_write(
            fd, data)

    def send_to_bot(self, msg):
        if not self._fd:
            print "not fd yet.."
            return
        print "SENDING TO BOT: ", msg, self._fd
        self.sock.send(self.pack_bot_msg(msg) + "\n")

    def start_main_loop(self):
        self._server_thread = threading.Thread(target=self._main_loop)
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()

    def _main_loop(self):
        if not self._fd:
            print "WAITING FOR CONNECTION..."
            time.sleep(0.5)
            self._main_loop()

        while not self.turn_event.is_set():
            # not in turn, wait
            time.sleep(0.1)
            if self.stop_event.is_set():
                self.send_to_bot("QUIT")
                self._server.shutdown()
                return

        if not self.turn_cookie:
            # Got a new turn cookie
            self.turn_cookie = self.queue.get()[1]

        print "is my turn!!", self.turn_cookie
        self.finish_turn()
        #self.send_to_bot("QUIT")
        self._main_loop()

        # Validate if this is my bot
        #if bot_data['bot_cookie'] != self.bot_cookie:
        #    self.logg("@@@@@@ BAD BOY! - INVALID BOT COOKIE")
        #    self.finish_turn()
        #    request.sendall(self.pack_bot_msg("INVALID BOT COOKIE"))
        #    return

        # validate if we are in a turn
        # if bot_data['turn_cookie'] == self.turn_cookie:
        #     # This is still my turn
        #     # The bot can take actions here
        #     #self.take_action(bot_data['action'], bot_data['action_args'])
        #     self.finish_turn()
        #     request.sendall(self.pack_bot_msg("DONE"))
        #     return
        # else:
        #     # First move of the turn
        #     # We should have a turn cookie now
        #     try:
        #         self.turn_cookie = self.queue.get_nowait()[1]
        #     except Empty, e:
        #         request.sendall(self.pack_bot_msg("NOT_YOUR_TURN"))
        #         return
        #     else:
        #         request.sendall(self.pack_bot_msg("TURN"))
        #         return

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


def bot_worker(bot_dict, bot_queue, turn_event, turn_done_event, std_out_queue, stop_event, port):
    bot_dir = os.path.abspath(os.path.dirname(bot_dict["bot_script"]))
    bot_file = os.path.basename(bot_dict["bot_script"])
    sandproc = SandboxedBoTController(bot_dict["bot_cookie"],
                                 bot_file,
                                 bot_queue,
                                 turn_event,
                                 turn_done_event,
                                 std_out_queue,
                                 stop_event,
                                 port,
                                 tmpdir=bot_dir)
    try:
        sandproc.interact()
    finally:
        sandproc.kill()

def run_match(players):
    std_out_queue = Queue()
    stop_event = Event()

    PORTS = range(9000, 9500)
    for bot_id in players.keys():
        players[bot_id]["queue"] = Queue()
        players[bot_id]["turn_done"] = Event()
        players[bot_id]["turn_event"] = Event()
        # create a bot id
        players[bot_id]["bot_cookie"] = get_cookie()
        copy_basebot(players[bot_id]["bot_script"],
                     players[bot_id]["bot_cookie"])
        
        p = Process(target=bot_worker, args=(players[bot_id],
                                             players[bot_id]["queue"],
                                             players[bot_id]["turn_event"],
                                             players[bot_id]["turn_done"],
                                             std_out_queue,
                                             stop_event,
                                             PORTS.pop()
                                             ))
        p.start()

    print "NOW START THE ROUNDS"

    for i in range(0, 10):
        std_out_queue.put("\n\nStarting round %s\n" % str(i))
        print "Starting round: ", i
        # 10 turns
        for k in players.keys():
            turn_cookie = get_cookie()
            std_out_queue.put("\n===== STARTED TURN %s FOR BOT %s" % (turn_cookie,
                                                                      players[k]["bot_cookie"]))
            print "\n===== STARTED TURN %s FOR BOT %s" % (turn_cookie, players[k]["bot_cookie"])
            players[k]["queue"].put(["TURN", turn_cookie])
            players[k]["turn_done"].clear()
            players[k]["turn_event"].set()

            # Wait for the player to finish...
            while players[k]["turn_event"].is_set():
                time.sleep(0.1)
            #players[k]["turn_done"].wait()

            std_out_queue.put("===== ENDED TURN %s FOR BOT %s" % (turn_cookie,
                                                                      players[k]["bot_cookie"]))
    # Exit
    stop_event.set()
    time.sleep(3)

    while not std_out_queue.empty():
        print std_out_queue.get()

    print "CLOSING..."

if __name__ == '__main__':
    run_match({1: {"bot_script": "bots/bot1/script.py"}, 2: {"bot_script": "bots/bot2/script.py"}})
