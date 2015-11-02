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


def unit_to_east(unit_coordinate):
    return (Coordinate(latitude, unit_coordinate.longitude) for latitude in
            range(unit_coordinate.latitude + 1, unit_coordinate.latitude + VISIBILITY_DISTANCE))


def unit_to_south(unit_coordinate):
    return (Coordinate(unit_coordinate.latitude, longitude) for longitude in
            range(unit_coordinate.longitude + 1, unit_coordinate.longitude + VISIBILITY_DISTANCE))


def unit_to_north(unit_coordinate):
    return (Coordinate(unit_coordinate.latitude, longitude) for longitude in
            range(unit_coordinate.longitude - VISIBILITY_DISTANCE, unit_coordinate.longitude))


def unit_to_west(unit_coordinate):
    return (Coordinate(latitude, unit_coordinate.longitude) for latitude in
            range(unit_coordinate.latitude - VISIBILITY_DISTANCE, unit_coordinate.latitude))


def get_unit_visibility(unit):
    tiles_in_view = [unit.coordinate]
    extended_tiles = []
    for cardinal in (unit_to_east, unit_to_south, unit_to_north, unit_to_west):
        extended_tiles.extend(cardinal(unit.coordinate))

    for coordinate in extended_tiles:
        if coord_in_arena(coord=coordinate, arena=unit.current_tile.arena):
            tiles_in_view.append(coordinate)

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
        self._matrix = [[TileContainer(self) for __ in range(width)] for _ in range(height)]

    def pprint(self):
        pprint.pprint(self._matrix)

    @staticmethod
    def calculate_visible_tiles_for_player(bot):
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

        for coordinate in visible_tiles:
            map_copy[coordinate.longitude][coordinate.latitude] = str(self.get_tile_content(coordinate))

        return map_copy

    def add_units_to_player(self, bot, amount_of_units=STARTS_WITH_N_UNITS, garrisoned=True):
        for i in range(amount_of_units):
            if garrisoned:
                initial_location = bot.hq.coordinate
            else:
                # random location in the open
                initial_location = self.get_random_free_tile()

            new_unit = AttackUnit(initial_location, bot.p_num)
            self.set_content_on_tile(initial_location, new_unit)
            bot.add_unit(new_unit)

    def random_initial_player_location(self, bot):
        slot_size = self.height // 3
        latitude = random.choice(range(self.width))

        if bot.p_num % 2 == 0:
            # even player numbers go to the top side of the map
            longitude = random.choice(range(slot_size))
        else:
            # odd player numbers go to the bottom side of the map
            longitude = random.choice(range(self.height - slot_size, self.height))

        initial_player_coord = Coordinate(latitude, longitude)

        player_hq = HeadQuarter(initial_player_coord, bot.p_num, STARTS_WITH_N_UNITS)
        self.set_content_on_tile(initial_player_coord, player_hq)
        bot.hq = player_hq

        return initial_player_coord

    def move(self, unit, from_coord, to_coord):
        self.remove_content_from_tile(from_coord, unit)
        self.set_content_on_tile(to_coord, unit)

    def get_tile_content(self, coordinate):
        return self._matrix[coordinate.longitude][coordinate.latitude]

    def set_content_on_tile(self, coordinate, content):
        self._matrix[coordinate.longitude][coordinate.latitude].add_item(content)

    def number_of_units_in_tile(self, coordinate):
        return len(self.get_tile_content(coordinate).items)

    def remove_content_from_tile(self, coordinate, content):
        self._matrix[coordinate.longitude][coordinate.latitude].remove_item(content)

    def is_free_tile(self, coordinate):
        return not self._matrix[coordinate.longitude][coordinate.latitude].items

    def get_random_free_tile(self):
        random_coordinate = Coordinate(latitude=random.choice(range(self.width)),
                                       longitude=random.choice(range(self.height)))

        if self.is_free_tile(random_coordinate):
            return random_coordinate
        else:
            return self.get_random_free_tile()

    def get_unit(self, content):
        for row in self._matrix:
            for tile in row:
                for item in tile.items:
                    if str(item.id) == str(content):
                        return item
