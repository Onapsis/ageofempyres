import pprint
import json
from turnboxed.gamecontroller import BaseGameController
import random
from collections import defaultdict


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


def get_unit_visibility(unit):
    tiles_in_view = [(unit.x, unit.y)]
    extended_tiles = []

    # to the east
    for x in range(unit.x + 1, unit.x + VISIBILITY_DISTANCE):
        extended_tiles.append((x, unit.y))

    # to the south
    for y in range(unit.y + 1, unit.y + VISIBILITY_DISTANCE):
        extended_tiles.append((unit.x, y))

    # to the north
    for y in range(unit.y - VISIBILITY_DISTANCE, unit.y):
        extended_tiles.append((unit.x, y))

    # to the west
    for x in range(unit.x - VISIBILITY_DISTANCE, unit.x):
        extended_tiles.append((x, unit.y))

    for i in extended_tiles:
        if i[0] >= 0 and i[1] >= 0 and i[1] < unit.container.arena.width\
                and i[0] < unit.container.arena.height:
            tiles_in_view.append(i)

    return tiles_in_view


class BaseUnit(object):

    def __init__(self, x, y, p_num):
        self.x = x
        self.y = y
        self.container = None
        self.player_id = p_num


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
        #self.matrix = {}
        #for r in range(self.height):
        #    self.matrix[r] = [FREE for x in range(self.width)]

    def pprint(self):
        pprint.pprint(self.matrix)

    def get_fog_mask_for_player(self, bot):
        visible_tiles = []
        visible_tiles.extend(get_unit_visibility(bot.hq))
        for unit in bot.units:
            visible_tiles.extend(get_unit_visibility(unit))

        return visible_tiles

    def get_map_for_player(self, bot):
        fog_mask = self.get_fog_mask_for_player(bot)

        map_copy = [[FOG_CONSTANT for x in range(self.width)] for x in range(self.height)]
        #map_copy = self.matrix.copy()
        for x, y in fog_mask:
            map_copy[y][x] = str(self.matrix[y][x])

        print json.dumps(map_copy)
        return map_copy

    def get_random_free_tile(self):
        _x = random.choice(range(self.width))
        _y = random.choice(range(self.height))
        if self.matrix[_y][_x] == 0:
            return _x, _y
        else:
            return self.get_random_free_tile()

    def add_initial_units_to_player(self, bot):
        garrisoned = False
        for i in range(INITIAL_UNITS):
            if garrisoned:
                new_unit = AttackUnit(bot.hq.x, bot.hq.y, bot.p_num)
                bot.add_unit(new_unit)
                bot.hq.garrison_unit(new_unit)
            else:
                # random location in the open
                x, y = self.get_random_free_tile()
                new_unit = AttackUnit(x, y, bot.p_num)
                container = TileContainer(self)
                container.add_item(new_unit)
                self.matrix[y][x] = container

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


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.arena = ArenaGrid()
        self.bots = bots
        self.rounds = 10

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
        bot = self.get_bot(bot_cookie)
        if "EXCEPTION" in request.keys():
            # bot failed in turn
            self.log_msg("Bot %s crashed: %s %s" % (bot.username, request['EXCEPTION'], request['TRACEBACK']))
            self.stop()
            return -1
        else:
            self.log_msg("GOT Action: %s" % request['MSG'])

        return 0

    def get_turn_data(self, bot_cookie):
        bot = self.get_bot(bot_cookie)
        # this should return the data sent to the bot
        # on each turn
        feedback = {"map": self.arena.get_map_for_player(bot), 'player_num': bot.p_num}
        #self.log_msg("MAP FOR BOT %s:" % bot.p_num)
        #self.log_msg(pprint.pformat(self.arena.get_map_for_player(bot)))
        #feedback = {"map": None}
        #self.log_msg("FEEDBACK: " + str(feedback))
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