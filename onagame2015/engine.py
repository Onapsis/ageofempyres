import pprint
import json
from turnboxed.gamecontroller import BaseGameController
import random
from collections import namedtuple
from onagame2015.actions import BaseBotAction, AttackAction, MoveAction

AVAILABLE_MOVEMENTS = ((0, 1), (0, -1), (1, 0), (-1, 0))
Coordinate = namedtuple('Coordinate', 'x y')


def unit_in_coord(coord, unit):
    return (
        0 <= coord.x < unit.container.arena.height and
        0 <= coord.y < unit.container.arena.width)


class InvalidBotOutput(Exception):
    reason = u'Invalid output'


class BotTimeoutException(Exception):
    reason = u'Timeout'


class GameOverException(Exception):
    pass


# Constants we use in the game
FREE = 0
UNAVAILABLE_TILE = 1
FOG_CONSTANT = "F"
VISIBILITY_DISTANCE = 3
INITIAL_UNITS = 5


def unit_to_east(unit):
    return ((x, unit.y) for x in range(unit.x + 1, unit.x + VISIBILITY_DISTANCE))


def unit_to_south(unit):
    return ((unit.x, y) for y in range(unit.y + 1, unit.y + VISIBILITY_DISTANCE))


def unit_to_north(unit):
    return ((unit.x, y) for y in range(unit.y - VISIBILITY_DISTANCE, unit.y))


def unit_to_west(unit):
    return ((x, unit.y) for x in range(unit.x - VISIBILITY_DISTANCE, unit.x))


def get_unit_visibility(unit):
    tiles_in_view = [(unit.x, unit.y)]
    extended_tiles = []
    for cardinal in (unit_to_east, unit_to_south, unit_to_north, unit_to_west):
        extended_tiles.extend(cardinal(unit))

    for x, y in extended_tiles:
        if unit_in_coord(Coordinate(x, y), unit):
            tiles_in_view.append((x, y))

    return tiles_in_view


class BaseUnit(object):

    def __init__(self, x, y, player_id):
        self.id = id(self)
        self.x = x
        self.y = y
        self.container = None
        self.player_id = player_id


class TileContainer(object):

    def __init__(self, arena):
        self.arena = arena
        self._items = []

    def add_item(self, item):
        item.container = self
        self._items.append(item)

    def remove_item(self, item):
        self._items = [i for i in self._items if i.id != item.id]

    @property
    def items(self):
        return self._items

    def __repr__(self):
        return ','.join([str(i) for i in self._items])


class HeadQuarter(BaseUnit):

    def __init__(self, x, y, player_id, initial_units):
        super(HeadQuarter, self).__init__(x, y, player_id)
        self.units = initial_units

    def __repr__(self):
        return 'HQ:{}Id:{}'.format(self.player_id, self.id)

    def garrison_unit(self, unit):
        self.container.add_item(unit)


class BlockedPosition(BaseUnit):

    def __init__(self, x, y, rep):
        super(BlockedPosition, self).__init__(x, y, None)
        self.rep = rep

    def __repr__(self):
        return '%s' % self.rep


class AttackUnit(BaseUnit):

    def __repr__(self):
        return 'U:{}Id:{}'.format(self.player_id, self.id)

    def move(self, direction):
        """Move attacker into new valid position:
        # Direction must be one of ((0, 1), (0, -1), (1, 0), (-1, 0))
        # New position must be part of the arena grid
        # New position must be occupied by other attack unit of same player, or empty
        """
        # Direction must be one of
        assert direction in AVAILABLE_MOVEMENTS

        self.x += direction[0]
        self.y += direction[1]

        # Test if position is in range
        assert 0 <= self.x < self.container.arena.width
        assert 0 <= self.y < self.container.arena.height

        # Test if all occupiers are of the same team of this player (could be zero, or more)
        tile = self.container.arena.matrix[self.x][self.y]
        assert all(x.player_id == self.player_id for x in tile.items)

        # Move from current position to next one
        self.container.remove_item(self)
        tile.add_item(self)


class ArenaGrid(object):
    """
    The grid that represents the arena over which the players are playing.
    """
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.matrix = [[TileContainer(self) for _ in range(self.width)] for _ in range(self.height)]

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
        for x, y in fog_mask:
            map_copy[y][x] = str(self.matrix[y][x])

        print json.dumps(map_copy)
        return map_copy

    def get_random_free_tile(self):
        _x = random.choice(range(self.width))
        _y = random.choice(range(self.height))
        if not self.matrix[_y][_x].items:
            return _x, _y
        else:
            return self.get_random_free_tile()

    def add_initial_units_to_player(self, bot):
        garrisoned = True
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

    def get_unit(self, unit_id):
        for row in self.matrix:
            for tile in row:
                for unit in tile.items:
                    if str(unit.id) == str(unit_id):
                        return unit

    def random_initial_player_location(self, bot):
        slot_size = self.height / 3
        x = random.choice(range(self.width))

        if bot.p_num % 2 == 0:
            # even player numbers go to the top side of the map
            y = random.choice(range(slot_size))
        else:
            # odd player numbers go to the bottom side of the map
            y = random.choice(range(self.height - slot_size, self.height))

        tile = self.matrix[y][x]
        player_hq = HeadQuarter(x, y, bot.p_num, 5)  # FIXME: Make 5 configurable
        tile.add_item(player_hq)
        bot.hq = player_hq


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.arena = ArenaGrid()
        self.bots = bots
        self.rounds = 10
        self._json = {}
        self._actions = {cls.ACTION_NAME: cls for cls in BaseBotAction.__subclasses__()}

        # set initial player locations
        for bot in self.bots:
            # Set the player HeadQuarter location
            self.arena.random_initial_player_location(bot)
            self.arena.add_initial_units_to_player(bot)
        self.arena.pprint()

    @property
    def json(self):
        return json.dumps(self._json)

    def get_bot(self, bot_cookie):
        bot_name = self.players[bot_cookie]['player_id']
        for b in self.bots:
            if b.username == bot_name:
                return b
        return None

    @staticmethod
    def _validate_actions(actions):
        """Check if actions follow all rules:
        # It must be at least one movement
        # One soldier could move only once
        #TODO: If once soldier attack, he couldn't move

        :param actions: list of actions
        :return: None, raise an Exception if some rule is broken
        """
        moved_units = []
        for action in actions:
            if action['action_type'] == MoveAction.ACTION_NAME:
                if action['unit_id'] in moved_units:
                    raise Exception('Error: Unit {unit_id} moved twice'.format(action))

                moved_units.append(action['unit_id'])
            else:
                raise Exception('Unknown move: "{action_type}"'.format(action))

        if not moved_units:
            raise Exception('It must be at least one movement')

    def _update_game_status(self, action_key, new_status):
        pass

    def evaluate_turn(self, request, bot_cookie):
        # Game logic here. Return should be an integer."
        bot = self.get_bot(bot_cookie)
        if "EXCEPTION" in request.keys():
            # bot failed in turn
            self.log_msg("Bot %s crashed: %s %s" % (bot.username, request['EXCEPTION'], request['TRACEBACK']))
            self.stop()
            return -1
        self.log_msg("GOT Action: %s" % request['MSG']['ACTIONS'])
        for action in request['MSG']['ACTIONS']:
            bot_action_type = self._actions.get(action['action_type'], BaseBotAction)
            bot = self.get_bot(bot_cookie)
            result = bot_action_type(bot).execute(self.arena, action)
            self._update_game_status(action['action_type'], result)
        return 0

    def get_turn_data(self, bot_cookie):
        """Feedback
        :return: the data sent to the bot on each turn
        """
        bot = self.get_bot(bot_cookie)
        return {
            'map': self.arena.get_map_for_player(bot),
            'player_num': bot.p_num,
        }


class BotPlayer(object):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq = None
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)
