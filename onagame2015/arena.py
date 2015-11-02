import pprint
import random
import itertools

from onagame2015.units import AttackUnit, HeadQuarter
from onagame2015.validations import coord_in_arena
from onagame2015.lib import (
    GameBaseObject,
    Coordinate,
    FOG_CONSTANT,
    STARTS_WITH_N_UNITS,
    VISIBILITY_DISTANCE,
)


def get_unit_visibility(unit):
    tiles_in_view = [unit.coordinate]
    west_to_east = [i for i in range(unit.coordinate.latitude - VISIBILITY_DISTANCE,
                                     unit.coordinate.latitude + VISIBILITY_DISTANCE+1)]
    south_to_north = [i for i in range(unit.coordinate.longitude - VISIBILITY_DISTANCE,
                                       unit.coordinate.longitude + VISIBILITY_DISTANCE+1)]

    for latitude, longitude in itertools.product(west_to_east, south_to_north):
        coordinate = Coordinate(latitude, longitude)
        if coord_in_arena(coord=coordinate, arena=unit.arena):
            tiles_in_view.append(coordinate)

    return tiles_in_view


class TileContainer(GameBaseObject):

    def __init__(self, arena):
        self.arena = arena
        self._items = []

    def add_item(self, item):
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

    def __getitem__(self, coordinate):
        return self._matrix[coordinate.longitude][coordinate.latitude]

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
        new_group_status = []
        for i in range(amount_of_units):
            if garrisoned:
                initial_location = bot.hq.coordinate
            else:
                # random location in the open
                initial_location = self.get_random_free_tile()

            new_unit = AttackUnit(initial_location, bot.p_num, arena=self)
            self.set_content_on_tile(initial_location, new_unit)
            bot.add_unit(new_unit)

            """ UNCOMMENT WHEN GAME STATUS FINISHED
            new_status = {
                    "action": "ADD_UNITS",
                    "player": bot.p_num,
                    "tile": {
                        "x": initial_location.latitude,
                        "y": initial_location.longitude,
                    },
                    "units": 1
            }
            new_group_status.append(new_status)"""

        return new_group_status

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

        player_hq = HeadQuarter(initial_player_coord, bot.p_num, STARTS_WITH_N_UNITS, arena=self)
        self.set_content_on_tile(initial_player_coord, player_hq)
        bot.hq = player_hq

        return initial_player_coord

    def move(self, unit, from_coord, to_coord):
        self.remove_content_from_tile(from_coord, unit)
        self.set_content_on_tile(to_coord, unit)

    def get_tile_content(self, coordinate):
        return self[coordinate]

    def set_content_on_tile(self, coordinate, content):
        self[coordinate].add_item(content)

    def number_of_units_in_tile(self, coordinate):
        return len(self.get_tile_content(coordinate).items)

    def remove_content_from_tile(self, coordinate, content):
        self[coordinate].remove_item(content)

    def is_free_tile(self, coordinate):
        return not self[coordinate].items

    def whos_in_tile(self, coordinate):
        """Return the player_id for the user that is in the given
        coordinate."""
        try:
            return next(unit.player_id for unit in self[coordinate].items)
        except StopIteration:
            return None

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
