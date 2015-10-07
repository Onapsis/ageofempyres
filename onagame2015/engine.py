import json
from turnboxed.gamecontroller import BaseGameController


class InvalidBotOutput(Exception):
    reason = u'Invalid output'
    pass


class BotTimeoutException(Exception):
    reason = u'Timeout'
    pass


class GameOverException(Exception):
    pass


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.bots = bots
        self.rounds = 100

    def get_json(self):
        return json.dumps({})

    def get_bot(self, bot_cookie):
        bot_name = self.players[bot_cookie]['player_id']
        for b in self.bots:
            if b.username == bot_name:
                return b
        return None

    def evaluate_turn(self, request, bot_cookie):
        # Game logic here. Return should be an integer."
        #bot = self.get_bot(bot_cookie)
        if "EXCEPTION" in request.keys():
            # bot failed in turn
            self.log_msg("Bot crashed: " + request['EXCEPTION'])
            self.stop()
        else:
            self.log_msg("GOT Action: %s" % request['MSG'])

        return 0

    def get_turn_data(self, bot_cookie):
        bot = self.get_bot(bot_cookie)
        # this should return the data sent to the bot
        # on each turn
        feedback = {"map": None}
        self.log_msg("FEEDBACK: " + str(feedback))
        return feedback


class BotPlayer(object):

    def __init__(self, bot_name, script):
        self.script = script
        self.username = bot_name