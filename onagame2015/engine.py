import pprint
import random
from turnboxed.gamecontroller import BaseGameController
from onagame2015.actions import BaseBotAction, MoveAction
from onagame2015.validations import coord_in_arena
from onagame2015.status import GameStatus
from onagame2015.lib import (
    Coordinate,
    GameStages,
    FREE,
    UNAVAILABLE_TILE,
    FOG_CONSTANT,
    VISIBILITY_DISTANCE,
    InvalidBotOutput,
    BotTimeoutException,
    GameOverException,
    STARTS_WITH_N_UNITS,
    AVAILABLE_MOVEMENTS,
)


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
        if coord_in_arena(coord=Coordinate(x, y), arena=unit.current_tile.arena):
            tiles_in_view.append((x, y))

    return tiles_in_view


class GameBaseObject(object):

    def __json__(self):
        """To be implemented by each object that wants to participate on the
        game result."""
        return {}


class BaseUnit(GameBaseObject):

    def __init__(self, x, y, player_id):
        self.id = id(self)
        self.x = x
        self.y = y
        self.current_tile = None
        self.player_id = player_id


class TileContainer(GameBaseObject):

    def __init__(self, arena):
        self.arena = arena
        self._items = []

    def add_item(self, item):
        item.current_tile = self
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
        self.current_tile.add_item(unit)


class BlockedPosition(BaseUnit):

    def __init__(self, x, y, rep):
        super(BlockedPosition, self).__init__(x, y, None)
        self.rep = rep

    def __repr__(self):
        return '%s' % self.rep


class AttackUnit(BaseUnit):

    def __repr__(self):
        return 'U:{}Id:{}'.format(self.player_id, self.id)

    def __json__(self):
        return {'key': 'AttackUnit'}

    def move(self, direction):
        """Move attacker into new valid position:
        # Direction must be one of ((0, 1), (0, -1), (1, 0), (-1, 0))
        # New position must be part of the arena grid
        # New position must be occupied by other attack unit of same player, or empty
        """
        # Direction must be one of
        if tuple(direction) not in AVAILABLE_MOVEMENTS:
            raise Exception('Direction must be one of: "{}" and "{}" found'.format(AVAILABLE_MOVEMENTS, direction))

        x = self.x + direction[0]
        y = self.y + direction[1]

        # Test if position is in range
        if not (0 <= x < self.current_tile.arena.width and 0 <= y < self.current_tile.arena.height):
            raise Exception('Invalid position ({}, {})'.format(x, y))

        # Test if all occupiers are of the same team of this player (could be zero, or more)
        tile_destination = self.current_tile.arena.matrix[y][x]
        if not self.can_invade(tile_destination):
            raise Exception('All occupiers must be of the same team')

        self.x = x
        self.y = y
        # Move from current position to next one
        self.current_tile.remove_item(self)
        tile_destination.add_item(self)

    def can_invade(self, tile):
        # TODO: handle enemy HQ invasion
        return all(unit.player_id == self.player_id for unit in tile.items)


class ArenaGrid(GameBaseObject):
    """
    The grid that represents the arena over which the players are playing.
    """
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.matrix = [[TileContainer(self) for __ in range(self.width)] for _ in range(self.height)]

    def pprint(self):
        pprint.pprint(self.matrix)

    def calculate_visible_tiles_for_player(self, bot):
        """
        Calculate based in the HQ and units of the bot
        @return: <list> of <tuples>
        [(x0, y0), (x1, y1),....]
        Each tuple represents a tile that the player is able to see.
        """
        visible_tiles = []
        visible_tiles.extend(get_unit_visibility(bot.hq))
        for unit in bot.units:
            visible_tiles.extend(get_unit_visibility(unit))

        return visible_tiles

    def get_map_for_player(self, bot):
        visible_tiles = self.calculate_visible_tiles_for_player(bot)

        map_copy = [[FOG_CONSTANT for __ in range(self.width)] for _ in range(self.height)]
        for x, y in visible_tiles:
            map_copy[y][x] = str(self.matrix[y][x])

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
        for i in range(STARTS_WITH_N_UNITS):
            if garrisoned:
                new_unit = AttackUnit(bot.hq.x, bot.hq.y, bot.p_num)
                bot.add_unit(new_unit)
                bot.hq.garrison_unit(new_unit)
            else:
                # random location in the open
                x, y = self.get_random_free_tile()
                new_unit = AttackUnit(x, y, bot.p_num)
                tile = TileContainer(self)
                tile.add_item(new_unit)
                self.matrix[y][x] = tile

    def get_unit(self, unit_id):
        for row in self.matrix:
            for tile in row:
                for unit in tile.items:
                    if str(unit.id) == str(unit_id):
                        return unit

    def random_initial_player_location(self, bot):
        slot_size = self.height // 3
        x = random.choice(range(self.width))

        if bot.p_num % 2 == 0:
            # even player numbers go to the top side of the map
            y = random.choice(range(slot_size))
        else:
            # odd player numbers go to the bottom side of the map
            y = random.choice(range(self.height - slot_size, self.height))

        tile = self.matrix[y][x]
        player_hq = HeadQuarter(x, y, bot.p_num, STARTS_WITH_N_UNITS)
        tile.add_item(player_hq)
        bot.hq = player_hq
        return x, y


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.arena = ArenaGrid()
        self.bots = bots
        self.rounds = 10
        self._actions = {cls.ACTION_NAME: cls for cls in BaseBotAction.__subclasses__()}
        self.game_status = GameStatus()
        self.deploy_players()

    def deploy_players(self):
        initial_status = {
            "map_source": "map1_100x100.json",
            "fog_range": 1,
            'players': [],
        }
        for bot, color in zip(self.bots, ("0x000077", "0xFF0000")):
            x, y = self.arena.random_initial_player_location(bot)
            self.arena.add_initial_units_to_player(bot)
            player_data = {
                'name': bot,
                'color': color,
                'position': {'x': x, 'y': y},
                'units': STARTS_WITH_N_UNITS,
            }
            initial_status['players'].append(player_data)
        self.game_status.add_game_stage(GameStages.INITIAL, initial_status)

    @property
    def json(self):
        return self.game_status.json

    def get_bot(self, bot_cookie):
        bot_name = self.players[bot_cookie]['player_id']
        try:
            return next(b for b in self.bots if b.username == bot_name)
        except StopIteration:
            raise RuntimeError("No bot named {}".format(bot_name))

    @staticmethod
    def _validate_actions(actions):
        """Check if actions follow all rules:
        # At least one movement must be done
        # Each soldier can move once
        #TODO: If a soldier attacks, he can't move.

        :param actions: list of actions
        :return: None, raise an Exception if some rule is broken
        """
        moved_units = []
        for action in actions:
            if action['action_type'] == MoveAction.ACTION_NAME:
                if action['unit_id'] in moved_units:
                    raise Exception('Error: Unit {unit_id} moved twice'.format(**action))

                moved_units.append(action['unit_id'])

        if not moved_units:
            raise Exception('At least one movement must be done')

    def _update_game_status(self, action_key, new_status):
        self.game_status.update_turns(action_key, new_status)

    def _handle_bot_failure(self, bot, request):
        """Manage the case if one of the bots failed,
        in that case, stop the execution, and log accordingly.
        """
        if "EXCEPTION" in request:
            # bot failed in turn
            self.log_msg("Bot %s crashed: %s %s" % (bot.username, request['EXCEPTION'], request['TRACEBACK']))
            self.stop()
            return -1

    def evaluate_turn(self, request, bot_cookie):
        """
        # Game logic here.
        @return: <int>
        """
        bot = self.get_bot(bot_cookie)
        if self._handle_bot_failure(bot, request) == -1:
            return -1

        self.log_msg("GOT Action: %s" % request['MSG']['ACTIONS'])
        self._validate_actions(request['MSG']['ACTIONS'])

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


class BotPlayer(GameBaseObject):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq = None
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)
