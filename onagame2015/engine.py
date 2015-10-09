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
FOG_CONSTANT = "F"
VISIBILITY_DISTANCE = 3
INITIAL_UNITS = 5


class BaseUnit(object):

    def __init__(self, x, y, p_num):
        self.x = x
        self.y = y
        self.container = None
        self.player_id = p_num

    def get_view_scope(self):
        tiles_in_view = [(self.x, self.y)]
        extended_tiles = []
        #for i in range(self.y - VISIBILITY_DISTANCE, self.y):
        #    extended_tiles.append((self.x, self.y - VISIBILITY_DISTANCE))
        #extended_tiles.append((self.x, self.y + VISIBILITY_DISTANCE))

        # to the east
        for x in range(self.x + 1, self.x + VISIBILITY_DISTANCE):
            extended_tiles.append((x, self.y))

        # to the south
        for y in range(self.y + 1, self.y + VISIBILITY_DISTANCE):
            extended_tiles.append((self.x, y))

        # to the north
        for y in range(self.y - VISIBILITY_DISTANCE, self.y):
            extended_tiles.append((self.x, y))

        # to the west
        for x in range(self.x - VISIBILITY_DISTANCE, self.x):
            extended_tiles.append((x, self.y))

        #extended_tiles.append((self.x - VISIBILITY_DISTANCE, self.y))

        for i in extended_tiles:
            if i[0] >= 0 and i[1] >= 0 and i[1] < self.container.arena.width\
                    and i[0] < self.container.arena.height:
                tiles_in_view.append(i)
        #print tiles_in_view
        return tiles_in_view


class TileContainer(object):

    def __init__(self, arena):
        self.arena = arena
        self._items = []

    def add_item(self, item):
        item.container = self
        self._items.append(item)

    def __repr__(self):
        return ','.join([str(i) for i in self._items])


class HQ(BaseUnit):

    def __init__(self, x, y, p_num):
        BaseUnit.__init__(self, x, y, p_num)

    def __repr__(self):
        return 'HQ:%s' % self.player_id

    def garrison_unit(self, unit):
        self.container.add_item(unit)


class AttackUnit(BaseUnit):

    def __init__(self, x, y, p_num):
        BaseUnit.__init__(self, x, y, p_num)

    def __repr__(self):
        return 'U:%s' % self.player_id


class ArenaGrid(object):
    """
    The grid that represents the arena over which the players are playing.
    """
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.matrix = [[FREE for x in range(self.width)] for x in range(self.height)]

    def pprint(self):
        pprint.pprint(self.matrix)

    def get_fog_mask_for_player(self, bot):
        visible_tiles = []
        visible_tiles.append((bot.hq.x, bot.hq.y))
        for unit in bot.units:
            visible_tiles.extend(unit.get_view_scope())

        return visible_tiles

    def get_map_for_player(self, bot):
        fog_mask = self.get_fog_mask_for_player(bot)

        map_copy = [[FOG_CONSTANT for x in range(self.width)] for x in range(self.height)]
        for x, y in fog_mask:
            map_copy[y][x] = self.matrix[y][x]

        return map_copy

    def get_random_free_tile(self):
        _x = random.choice(range(self.width))
        _y = random.choice(range(self.height))
        if self.matrix[_y][_x] == 0:
            return _x, _y
        else:
            return self.get_random_free_tile()

    def add_initial_units_to_player(self, bot):
        for i in range(INITIAL_UNITS):
            x, y = self.get_random_free_tile()
            #new_unit = AttackUnit(bot.hq.x, bot.hq.y, bot.p_num)
            new_unit = AttackUnit(x, y, bot.p_num)
            container = TileContainer(self)
            container.add_item(new_unit)
            self.matrix[y][x] =\
                container
            bot.add_unit(new_unit)
            #bot.hq.garrison_unit(new_unit)

    def random_initial_player_location(self, bot):
        slot_size = self.height / 3
        x = random.choice(range(self.width))

        if (bot.p_num % 2 == 0):
            # even player numbers go to the top side of the map
            y = random.choice(range(slot_size))
        else:
            # odd player numbers go to the bottom side of the map
            y = random.choice(range(self.height - slot_size, self.height))

        new_tile = TileContainer(self)
        player_hq = HQ(x, y, bot.p_num)
        new_tile.add_item(player_hq)
        self.matrix[y][x] = new_tile
        bot.hq = player_hq

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
        self.rounds = 1

        # set initial player locations
        for bot in self.bots:
            # Set the player HQ location
            self.arena.random_initial_player_location(bot)
            self.arena.add_initial_units_to_player(bot)
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
        #feedback = {"map": self.arena.get_map_for_player(bot)}
        self.log_msg("MAP FOR BOT %s:" % bot.p_num)
        self.log_msg(pprint.pformat(self.arena.get_map_for_player(bot)))
        feedback = {"map": None}
        self.log_msg("FEEDBACK: " + str(feedback))
        return feedback


class BotPlayer(object):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq = None
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)