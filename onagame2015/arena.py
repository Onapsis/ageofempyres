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
    farthest_from_point,
    BOT_COLORS,
    UNIT_TYPE_ATTACK,
    UNIT_TYPE_HQ,
    AVAILABLE_MOVEMENTS,
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

    def __init__(self, arena, reachable):
        self.arena = arena
        self.reachable = reachable
        self._items = []

    def add_item(self, item):
        self._items.append(item)

    def remove_item(self, item):
        self._items = [i for i in self._items if i.id != item.id]

    def pop_one_unit(self):
        """Remove one unit from this tile.
        Invariant:
           pre-condition: len(self._items) == n AND n > 0
           condition: remove one unit
           post-condition: len(self._items) == n - 1
        """
        if not self._items:
            return
        random_unit = self._get_random_unit()
        if not random_unit:
            return
        self._items.remove(random_unit)
        return random_unit

    def _get_random_unit(self):
        """
        Get the first unit from the items list that belongs to the Attack Type
        :return: AttackUnit
        """
        for unit in self._items:
            if unit.type == UNIT_TYPE_ATTACK:
                return unit
        return None

    @property
    def items(self):
        return self._items

    @property
    def empty(self):
        """Returns true if not units present"""
        return all(item.type != UNIT_TYPE_ATTACK for item in self.items)

    def __repr__(self):
        if not self.reachable:
            return 'B'
        return ','.join([str(i) for i in self._items])

    def hq_for(self, player_id):
        return any(
            (i.type == UNIT_TYPE_HQ and i.player_id == player_id for i in self.items)
        )


class ArenaGrid(GameBaseObject):
    """
    The grid that represents the arena over which the players are playing.
    """
    def __init__(self, game_map, game_status):
        self._game_status = game_status
        self.width = game_map.width
        self.height = game_map.height
        self.eligible_hqs = game_map.eligible_hqs
        self._matrix = [
            [TileContainer(self, reachable) for reachable in row] for row in game_map.iterrows()
        ]

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

    def add_units_to_player(self, bot, amount_of_units=STARTS_WITH_N_UNITS):
        """Sets the units for the player, one inside de base and the others arround"""

        initial_location = bot.hq.coordinate
        elegible_tiles = tuple(self.elegible_tiles_for_units(initial_location))
        for i in range(amount_of_units):
            if i == 0:
                position = initial_location
            else:
                position = elegible_tiles[i % len(elegible_tiles)]

            new_unit = AttackUnit(position, bot.p_num, arena=self)
            self.set_content_on_tile(position, new_unit)
            bot.add_unit(new_unit)

    def elegible_tiles_for_units(self, initial_location):
        """Returns a generator over elegible places to put units"""
        for direction in AVAILABLE_MOVEMENTS:
            try:
                position = initial_location + direction
                cell = self[position]
                if cell.reachable:
                    yield  position
            except IndexError:
                continue

    def deploy_players(self, bot_list):
        """Receive a list of bots, and deploy them in the arena.
        Pick a headquarter location for the first bot, from the eligible
        options. Then, the second bot, will be placed as far as possible from
        the first one.
        @return: A dict indicating the players and where they were deployed in
        the map, to use as initial status for the game.
        {
         'players': [
          {'name': <bot_name>,
           'color': <color_for_player>,
           'position': {'x': <bot.latitude>, 'y': <bot.longitude>,
           'units': <n> :int> STARTS_WITH_N_UNITS,
           },
           ...
         ]
        }
        """
        first_bot, second_bot = bot_list
        eligible_hqs = list(self.eligible_hqs)
        random.shuffle(eligible_hqs)
        first_bot_location = eligible_hqs.pop()
        second_bot_location = farthest_from_point(first_bot_location, eligible_hqs)
        players = []
        for bot, location in zip((first_bot, second_bot), (first_bot_location, second_bot_location)):
            headquarter = HeadQuarter(location, bot.p_num, STARTS_WITH_N_UNITS, arena=self)
            self.set_content_on_tile(location, headquarter)
            bot.hq = headquarter
            players.append({
                'name': bot.username,
                'id': bot.p_num,
                'color': random.choice(BOT_COLORS),
                'position': {'x': location.latitude, 'y': location.longitude},
                'units': STARTS_WITH_N_UNITS,
            })
            self.add_units_to_player(bot)

        return {'players': players}

    def move(self, unit, from_coord, to_coord):
        self.remove_content_from_tile(from_coord, unit)
        self.set_content_on_tile(to_coord, unit)

    def get_tile_content(self, coordinate):
        return self[coordinate]

    def set_content_on_tile(self, coordinate, content):
        self[coordinate].add_item(content)

    def number_of_units_in_tile(self, coordinate):
        return sum(1 if unit.type == UNIT_TYPE_ATTACK else 0 for unit in self.get_tile_content(coordinate).items)

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

    def synchronize_attack_results(self, attack_result):
        """Receive a :dict: in <attack_result> and update the units in the
        coordinates according to the result.
        """
        units_removed = {}
        for who in ('attacker', 'defender'):
            loses = attack_result['{}_loses'.format(who)]
            coord = attack_result['{}_coord'.format(who)]
            units_removed['{}_removed_units'.format(who)] = self._remove_n_units_in_coord(coordinate=coord,
                                                                                          amount_to_remove=loses)
        return units_removed

    def _remove_n_units_in_coord(self, coordinate, amount_to_remove):
        units_popped = []
        for _ in range(amount_to_remove):
            units_popped.append(self[coordinate].pop_one_unit())
        return units_popped

    def get_unit(self, content):
        for row in self._matrix:
            for tile in row:
                for item in tile.items:
                    if str(item.id) == str(content):
                        return item

    def enemy_hq_taken(self, player, opponent):
        hq_tile_content = self.get_tile_content(opponent.hq.coordinate)
        return any(item.player_id == player.p_num for item in hq_tile_content.items)
