from onagame2015.validations import coord_in_arena, direction_is_valid
from onagame2015.lib import (
    GameBaseObject,
    Coordinate,
)


class BaseUnit(GameBaseObject):

    def __init__(self, coordinate, player_id):
        self.id = id(self)
        self.coordinate = coordinate
        self.current_tile = None
        self.player_id = player_id


class HeadQuarter(BaseUnit):

    def __init__(self, coordinate, player_id, initial_units):
        super(HeadQuarter, self).__init__(coordinate, player_id)
        self.units = initial_units

    def __repr__(self):
        return 'HQ:{}Id:{}'.format(self.player_id, self.id)

    def garrison_unit(self, unit):
        self.current_tile.add_item(unit)


class BlockedPosition(BaseUnit):

    def __init__(self, coordinate, rep):
        super(BlockedPosition, self).__init__(coordinate, None)
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
        # New position must be occupied by other attack unit of same player, or
        empty
        @return: :dict: indicating the destination and end
        {
           'from': <coord>,
           'to': <coord>,
        }
        """
        if not direction_is_valid(tuple(direction)):
            return {
                'from': self.coordinate,
                'to': self.coordinate,
                'error': 'Direction {} is invalid'.format(direction),
            }
        latitude = self.coordinate.latitude + direction[0]
        longitude = self.coordinate.longitude + direction[1]
        desired_coordinate = Coordinate(latitude, longitude)

        if not coord_in_arena(desired_coordinate, self.current_tile.arena):
            return {
                'from': self.coordinate,
                'to': self.coordinate,
                'error': 'Invalid position ({}, {})'.format(latitude, longitude),
            }

        tile_destination = self.current_tile.arena.get_tile_content(desired_coordinate)

        if not self.can_invade(tile_destination):
            return {
                'from': self.coordinate,
                'to': self.coordinate,
                'error': 'All occupiers must be of the same team',
            }

        # Move from current position to next one
        self.current_tile.arena.move(self, self.coordinate, desired_coordinate)
        origin = self.coordinate
        self.coordinate = desired_coordinate
        return {
            'from': origin,
            'to': self.coordinate,
            'error': '',
        }

    def can_invade(self, tile):
        # TODO: handle enemy HQ invasion
        return all(unit.player_id == self.player_id for unit in tile.items)
