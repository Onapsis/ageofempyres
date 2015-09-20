from sandboxengine.gamecontroller import BaseGameController


class PyTegGameController(BaseGameController):
    
    def __init__(self):
        BaseGameController.__init__(self)
        #super(PyTegGameController, self).__init__()

    def evaluate_turn(self, player, request):
        # Game logic here
        pass
