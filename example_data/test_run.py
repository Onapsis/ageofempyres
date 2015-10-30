import sys
from onagame2015.engine import BotPlayer, Onagame2015GameController


def main(argv):
    bot1_username = "user1"
    bot2_username = "user2"
    bots = [BotPlayer(bot1_username, argv[0], 1),
            BotPlayer(bot2_username, argv[1], 2)]

    game_instance = Onagame2015GameController(bots)
    for b in bots:
        game_instance.add_player(b.username, b.script)
    game_instance.run()

    json_data = game_instance.json
    print(json_data)

    sys.exit(0)


if __name__ == "__main__":
    main(["bots/bot1/script.py", "bots/bot1/script.py"])
