import os
import time
import SocketServer
import threading
import uuid
import json
from multiprocessing import Queue, Event, Process

from .playercontroller import SandboxedPlayerController


def get_cookie():
    return uuid.uuid4().hex[0:8]


class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(1024)
        print "RAW DATA FROM PLAYER CONTROLLER: ", data
        msg = json.loads(data)
        print "JSON FROM PLAYER CONTROLLER: ", msg, type(msg)
        # Ask the Game Controller to handle the player request
        bot_cookie = msg["BOT_COOKIE"]
        ret = self.server.game_controller.handle_player_request(msg["DATA"], bot_cookie)
        self.request.sendall(json.dumps(ret))


class BaseGameController:

    def __init__(self):
        self._server = None
        self._server_thread = None
        self.server_host = "localhost"
        self.server_port = 9999
        self.rounds = 100
        self.players = {}

        self.turns_queue = Queue()
        self.std_out_queue = Queue()
        #self.stop_event = Event()

    def log_msg(self, msg):
        self.std_out_queue.put(msg)

    def handle_player_request(self, data, bot_cookie):
        ret = self.evaluate_turn(data, self.players[bot_cookie])
        self.players[bot_cookie]["turn_event"].clear()
        return ret

    def evaluate_turn(self, player, request):
        raise NotImplementedError

    def _start_socket_server(self):
        # Create the server, binding to localhost
        self._server = SocketServer.TCPServer((self.server_host, self.server_port), MyTCPHandler)
        self._server.game_controller = self
        self.log_msg("Starting socket server..")
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()
        self.log_msg("Server loop running in thread: %s PORT: %s" % (self._server_thread.name, self.server_port))

    def add_player(self, player_id, player_script):
        bot_cookie = get_cookie()
        turn_event = Event()
        connected_event = Event()
        main_queue = Queue()
        self.players[bot_cookie] = {"player_id": player_id,
                                    "bot_cookie": bot_cookie,
                                    "player_script": player_script,
                                    "turn_event": turn_event,
                                    "connected_event": connected_event,
                                    "main_queue": main_queue}

    def run_player_process(self, player_d):
        p = SandboxedPlayerController(player_d["player_id"], os.path.abspath(player_d["player_script"]),
                                    player_d["bot_cookie"], player_d["turn_event"],
                                    player_d["connected_event"], player_d["main_queue"],
                                    self.std_out_queue)
        p.run_process()

    def run(self):
        self._start_socket_server()

        # Start all the sandbox processes
        for p_k in self.players.keys():
            self.log_msg("Starting player..")
            p = Process(target=self.run_player_process, args=(self.players[p_k],))
            p.start()

            # Wait for the sandbox process to connect to the controller.
            while not self.players[p_k]["connected_event"].is_set():
                # wait.. (possible timeout here)
                time.sleep(0.1)
            self.log_msg("Player %s connected" % self.players[p_k]["bot_cookie"])

        self.log_msg("Starting rounds")
        for i in range(0, self.rounds):
            self.log_msg("\n\nStarting round %s\n" % str(i))

            for p_k in self.players.keys():
                turn_cookie = get_cookie()
                self.log_msg("\n===== STARTED TURN %s FOR BOT %s" % (turn_cookie, self.players[p_k]["bot_cookie"]))
                self.players[p_k]["main_queue"].put({"MSG": "TURN", "DATA": turn_cookie})

                # Wait for the player to finish the turn...
                while self.players[p_k]["turn_event"].is_set():
                    # turnbased timeout check could go here
                    time.sleep(0.1)

                self.log_msg("===== ENDED TURN %s FOR BOT %s" % (turn_cookie, self.players[p_k]["bot_cookie"]))

        for p_k in self.players.keys():
            self.players[p_k]["main_queue"].put({"MSG": "QUIT"})

        self.log_msg("CLOSING..")
        # Exit

        self._server.shutdown()

        while self.std_out_queue.empty():
            print(self.std_out_queue.get())
