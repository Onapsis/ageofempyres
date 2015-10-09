import pprint
import copy
import json
from turnboxed.gamecontroller import BaseGameController
import random


class InvalidBotOutput(Exception):
    reason = u'Invalid output'
    pass


class BotTimeoutException(Exception):
    reason = u'Timeout'
    pass


class GameOverException(Exception):
    pass


# Constants we use in the game
FREE = 0
UNAVAILABLE_TILE = 1
FOG_CONSTANT = 2


class TileContainer(object):

    def __init__(self):
        self._items = []

    def add_item(self, item):
        self._items.append(item)

    def __repr__(self):
        return ','.join([str(i) for i in self._items])


class HQ(object):

    def __init__(self, p_num):
        self._player_id = p_num

    def __repr__(self):
        return 'HQ:%s' % self._player_id


class ArenaGrid(object):
    """
    The grid that represents the arena over which the players are playing.
    """
    def __init__(self, width=20, height=20):
        self.width = width
        self.height = height
        self.matrix = [[FREE for x in range(self.width)] for x in range(self.height)]

    def pprint(self):
        pprint.pprint(self.matrix)

    def get_fog_mask_for_player(self, bot):
        visible_tiles = []
        visible_tiles.append(bot.hq_x - FOG_CONSTANT)
        visible_tiles.append(bot.hq_y - FOG_CONSTANT)
        visible_tiles.append(bot.hq_x + FOG_CONSTANT)
        visible_tiles.append(bot.hq_y + FOG_CONSTANT)
        return [i for i in visible_tiles if i != 0 ]

    def get_map_for_player(self, bot):
        map_copy = copy.copy(self.matrix)
        for l_count in range(len(map_copy)):
            for t_count in range(len(map_copy[l_count])):
                if t_count != bot.p_num:
                    map_copy[l_count][t_count] = 0

        return map_copy

    def random_initial_player_location(self, player_num):
        slot_size = self.height / 3
        x = random.choice(range(self.width))
        new_tile = TileContainer()
        player_hq = HQ(player_num)
        new_tile.add_item(player_hq)

        if (player_num % 2 == 0):
            # even player numbers go to the top side of the map
            y = random.choice(range(slot_size))
            self.matrix[y][x] = new_tile
            return x, y
        else:
            # odd player numbers go to the bottom side of the map
            y = random.choice(range(self.height - slot_size, self.height))
            self.matrix[y][x] = new_tile
            return x, y

    # def copy_for_player(self):
    #     """Return just a copy of the portion we provide to the player."""
    #     return self.arena[:]
    #
    # def players_distance(self):
    #     """Return the distance between the bots. Only two players."""
    #     p1, p2 = [i for i in xrange(self.width) if self.arena[i] != FREE]
    #     return p2 - p1
    #
    # def __getitem__(self, (x, y)):
    #     return self.arena[x]
    #
    # def __setitem__(self, (x, y), value):
    #     self.arena[x] = value


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.arena = ArenaGrid()
        self.bots = bots
        self.rounds = 0

        # set initial player locations
        for p in self.bots:
            # Set the player HQ location
            p.hq_x, p.hq_y = self.arena.random_initial_player_location(p.p_num)
        self.arena.pprint()

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
        feedback = {"map": self.arena.get_map_for_player(bot)}
        self.log_msg("FEEDBACK: " + str(feedback))
        return feedback


class BotPlayer(object):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq_x = 0
        self.hq_y = 0