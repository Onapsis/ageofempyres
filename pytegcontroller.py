from turnboxed.gamecontroller import BaseGameController


class PyTegGameController(BaseGameController):
    
    def __init__(self):
        BaseGameController.__init__(self)
        self.rounds = 100

    def evaluate_turn(self, player, request):
        # Game logic here. Return should be an integer."
        return -1

    def get_turn_data(self, bot_cookie):
        # this should return the data sent to the bot
        # on each turn
        return None