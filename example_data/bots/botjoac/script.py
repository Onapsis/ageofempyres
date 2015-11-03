#import random
from basebot import BaseBot
import re


HQ = re.compile("HQ:(\d+)Id:(\d+)")
UNIT = re.compile("U:(\d+)Id:(\d+)")


def msvcrt_rand(seed):
    def rand():
        rand.seed = (214013*rand.seed + 2531011) & 0x7fffffff
        return rand.seed >> 16
    rand.seed = seed
    return rand


random = msvcrt_rand(123456)


def randint(start, end):
    d = end - start
    return start + random() % d


def choice(choices):
    return choices[randint(0, len(choices))]


def vector_sum(*args):
    return tuple(sum(n) for n in zip(*args))


class Tile(object):

    def __init__(self, tile_string, player_id):
        self.unit_ids = []
        self.enemies_count = 0
        self.enemy_hq = False
        self.own_hq = False
        self._parse_tile_string(tile_string, player_id)

    def _parse_tile_string(self, tile_string, player_id):
#        if tile_string and tile_string != 'F':
#            raise Exception(tile_string)
        player_id = str(player_id)
        for p_id, _ in HQ.findall(tile_string):
            if p_id == player_id:
                self.own_hq = True
            else:
                self.enemy_hq = True

        for p_id, unit_id in UNIT.findall(tile_string):
            if p_id == player_id:
                self.unit_ids.append(unit_id)
            else:
                self.enemies_count += 1


DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


class Unit(object):
    """Represents a Unit on the game"""

    def __init__(self, world, game_id):
        self.world = world
        self.game_id = game_id
        self.coords = None

    def move(self):
        self.world.actions.append({
            'action_type': 'MOVE',
            'unit_id': self.game_id,
            'direction': choice(DIRECTIONS),
        })


class Bot(BaseBot):

    def __init__(self):
        super(Bot, self).__init__()
        self.units = {}
        self.own_hq = None
        self.enemy_hq = None
        self.enemies = {}

    def on_turn(self, data_dict):
        self.update_state(data_dict)
        self.move_units()
        self.attack()
        return {'ACTIONS': self.actions}

    def update_state(self, data_dict):
        """Updates the state that the bot holds"""
        old_units = self.units

        self.actions = []
        self.units = {}
        self.enemies = {}
        self.player_id = data_dict['player_num']
        self.game_map = data_dict['map']
        for coords, tile in self.iterate_over_map_tiles():
            self.update_units(tile, coords, old_units)
            if tile.enemy_hq:
                self.enemy_hq = coords
            if tile.own_hq:
                self.own_hq = coords
            if tile.enemies_count:
                self.enemies[coords] = tile.enemies_count

    def update_units(self, tile, coords, old_units):
        """Update units based on the information for one tile"""
        for unit_id in tile.unit_ids:
            if unit_id in old_units:
                unit = old_units[unit_id]
            else:
                unit = Unit(self, unit_id)
            unit.coords = coords
            self.units[unit_id] = unit

    def iterate_over_map_tiles(self):
        """Returns a generator over the map tiles"""
        for y, row in enumerate(self.game_map):
            for x, tile_string in enumerate(row):
                yield (x, y), Tile(tile_string, self.player_id)

    def move_units(self):
        for unit in self.units.values():
            unit.move()

    def attack(self):
        for coords in {unit.coords for unit in self.units.values()}:
            target = self.select_target(coords)
            if target:
                self.actions.append({
                    'action_type': 'ATTACK',
                    'from': self.coords,
                    'to': target,
                })

    def select_target(self, coords):
        posible_targets = []
        for d in DIRECTIONS:
            t = vector_sum(coords, d)
            if t in self.enemies:
                posible_targets.append[t]

        if posible_targets:
            return choice(posible_targets)
