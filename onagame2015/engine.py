import pprint
import json
from turnboxed.gamecontroller import BaseGameController
import random
from collections import namedtuple
from onagame2015.actions import BaseBotAction


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
        return 'HeadQuarter:%s' % self.player_id

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
        return 'U:%s' % self.player_id

    def move(self, direction):
        d = direction.lower()
        if d in ('e', 'east'):
            self.x -= 1
        elif d in ('w', 'west'):
            self.x += 1
        elif d in ('n', 'north'):
            self.y -= 1
        elif d in ('s', 'south'):
            self.y += 1

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
    def __init__(self, width=100, height=100):
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
        # If once soldier attack, he couldn't move
        # If once soldier attack, he couldn't attack again

        :param actions: list of actions
        :return: None, raise an Exception if some rule is broken
        """

        # TODO: New positions of soldiers mustn't be occupied or blocked
        # TODO: All new positions of soldiers must be in the arena
        # TODO: When a soldier attack, the enemy must be front of him and it must be from other team

        # assert set(x['type'] for x in actions) == {'MOVE', 'ATTACK'}
        # assert any(True for x in actions if x['type'] == 'MOVE')

        moved_units = []
        attacked_units = []
        for action in actions:
            if action['type'] == 'MOVE':
                if action['id'] in moved_units:
                    raise Exception('Error: Unit {id} moved twice'.format(action))
                elif action['id'] in attacked_units:
                    raise Exception('Error: Unit {id} moved after an attack'.format(action))

                moved_units.append(action['id'])
            elif action['type'] == 'ATTACK':
                if action['id'] in attacked_units:
                    raise Exception('Error: Unit {id} attacked twice'.format(action))

                attacked_units.append(action['id'])
            else:
                raise Exception('Unknown move: "{type}"'.format(action))

        if not moved_units:
            raise Exception('It must be at least one movement')

    def _update_game_status(self, action_key, new_status):
        pass

    def evaluate_turn(self, request, bot_cookie):
        # Game logic here. Return should be an integer."
        if "EXCEPTION" in request.keys():
            # bot failed in turn
            self.log_msg("Bot crashed: " + request['EXCEPTION'])

            self.stop()
        else:
            self._validate_actions(request['actions'])
            self.log_msg("GOT Action: %s" % request['MSG'])
            for action_key in ('MOVE', 'ATTACK'):
                bot_action_type = self._actions.get(action_key, BaseBotAction)
                bot = self.get_bot(bot_cookie)
                result = bot_action_type(bot).execute()
                self._update_game_status(action_key, result)

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
