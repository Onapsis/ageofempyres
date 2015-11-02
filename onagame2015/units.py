from onagame2015.validations import coord_in_arena
from onagame2015.lib import (
    GameBaseObject,
    Coordinate,
    AVAILABLE_MOVEMENTS,
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
        # New position must be occupied by other attack unit of same player, or empty
        """
        print "1111111 MOVING UNIT IN DIRECTION {}".format(direction)
        # Direction must be one of
        if tuple(direction) not in AVAILABLE_MOVEMENTS:
            raise Exception('Direction must be one of: "{}" and "{}" found'.format(AVAILABLE_MOVEMENTS, direction))

        latitude = self.coordinate.latitude + direction[0]
        longitude = self.coordinate.longitude + direction[1]
        desired_coordinate = Coordinate(latitude, longitude)

        # Test if position is in range
        if not coord_in_arena(desired_coordinate, self.current_tile.arena):
            raise Exception('Invalid position ({}, {})'.format(desired_coordinate))

        # Test if all occupiers are of the same team of this player (could be zero, or more)
        tile_destination = self.current_tile.arena.get_tile_content(desired_coordinate)
        if not self.can_invade(tile_destination):
            raise Exception('All occupiers must be of the same team')

        # Move from current position to next one
        print 222222222222
        print "CURRENT_TILE {}".format(self.current_tile)
        print "ARENA TYPE {}".format(type(self.current_tile.arena))
        self.current_tile.arena.move(self, self.coordinate, desired_coordinate)
        print 333333333333
        self.coordinate = desired_coordinate

    def can_invade(self, tile):
        # TODO: handle enemy HQ invasion
        return all(unit.player_id == self.player_id for unit in tile.items)
