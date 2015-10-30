import pprint
import random

from onagame2015.units import AttackUnit, HeadQuarter
from onagame2015.validations import coord_in_arena
from onagame2015.lib import (
    GameBaseObject,
    Coordinate,
    FOG_CONSTANT,
    STARTS_WITH_N_UNITS,
    VISIBILITY_DISTANCE,
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
