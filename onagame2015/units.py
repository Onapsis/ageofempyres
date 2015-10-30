from onagame2015.lib import GameBaseObject
from onagame2015.lib import AVAILABLE_MOVEMENTS


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