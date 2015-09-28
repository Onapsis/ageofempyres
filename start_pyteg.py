from pytegcontroller import PyTegGameController

PLAYERS = [(1, "bots/bot1/script.py"),
           (2, "bots/bot2/script.py")]

if __name__ == '__main__':
    pyteg_game = PyTegGameController()
    for p_id, p_script in PLAYERS:
        pyteg_game.add_player(p_id, p_script)

    pyteg_game.run()