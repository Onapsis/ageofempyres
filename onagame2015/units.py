from onagame2015.lib import Coordinate
from onagame2015.lib import GameBaseObject
from onagame2015.lib import AVAILABLE_MOVEMENTS
from onagame2015.validations import coord_in_arena, direction_is_valid


class BaseUnit(GameBaseObject):

    def __init__(self, x, y, player_id):
        self.id = id(self)
        self.x = x
        self.y = y
        self.current_tile = None
        self.player_id = player_id


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
        @return: :dict: indicating the destination and end
        {
           'from': <coord>,
           'to': <coord>,
        }
        """
        origin = Coordinate(x=self.x, y=self.y)
        # Direction must be one of
        if not direction_is_valid(tuple(direction)):
            return {
                'from': origin,
                'to': origin,
                'error': 'Direction {} is invalid'.format(direction),
            }
        x = self.x + direction[0]
        y = self.y + direction[1]

        if not coord_in_arena(coord=Coordinate(x, y), arena=self.current_tile.arena):
            return {
                'from': origin,
                'to': origin,
                'error': 'Invalid position ({}, {})'.format(x, y),
            }

        tile_destination = self.current_tile.arena.matrix[y][x]
        if not self.can_invade(tile_destination):
            return {
                'from': origin,
                'to': origin,
                'error': 'All occupiers must be of the same team',
            }

        self.x = x
        self.y = y
        # Move from current position to next one
        self.current_tile.remove_item(self)
        tile_destination.add_item(self)
        return {
            'from': origin,
            'to': Coordinate(x=x, y=y),
            'error': '',
        }

    def can_invade(self, tile):
        # TODO: handle enemy HQ invasion
        return all(unit.player_id == self.player_id for unit in tile.items)
