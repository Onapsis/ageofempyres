from pytegcontroller import PyTegGameController
import shutil

PLAYERS = [(1, "bots/bot1/script.py"),
           (2, "bots/bot2/script.py")]

if __name__ == '__main__':
    shutil.copy("basebot.py", "bots/bot1/")
    shutil.copy("basebot.py", "bots/bot2/")
    pyteg_game = PyTegGameController()
    pyteg_game.rounds = 10
    for p_id, p_script in PLAYERS:
        pyteg_game.add_player(p_id, p_script)

    pyteg_game.run()