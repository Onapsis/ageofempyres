from basebot import BaseBot


class Mybot(BaseBot):

    def __init__(self):
        BaseBot.__init__(self)
        
    def on_turn(self, msg):
        if msg == "QUIT":
            print "EXITING.."
            return
        print "Turn data: ", msg
        #self.send_command("sarlanga")
        
a = Mybot()
