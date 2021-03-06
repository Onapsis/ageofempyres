from onagame2015.validations import coord_in_arena, direction_is_valid
from onagame2015.lib import (
    GameBaseObject,
    Coordinate,
    UNIT_TYPE_ATTACK,
    UNIT_TYPE_BLOCKED,
    UNIT_TYPE_HQ,
)


class BaseUnit(GameBaseObject):

    def __init__(self, coordinate, player_id, arena):
        self.id = id(self)
        self.coordinate = coordinate
        self.arena = arena
        self.player_id = player_id
        self.type = None


class HeadQuarter(BaseUnit):

    def __init__(self, coordinate, player_id, initial_units, arena):
        super(HeadQuarter, self).__init__(coordinate, player_id, arena)
        self.units = initial_units
        self.type = UNIT_TYPE_HQ

    def __repr__(self):
        return 'HQ:{}Id:{}'.format(self.player_id, self.id)

    def garrison_unit(self, unit):
        self.arena.set_content_on_tile(self.coordinate, unit)


class BlockedPosition(BaseUnit):

    def __init__(self, coordinate, arena, rep):
        super(BlockedPosition, self).__init__(coordinate, None, arena)
        self.rep = rep
        self.type = UNIT_TYPE_BLOCKED

    def __repr__(self):
        return '%s' % self.rep


class AttackUnit(BaseUnit):

    def __init__(self, coordinate, player_id, arena):
        super(AttackUnit, self).__init__(coordinate, player_id, arena)
        self.type = UNIT_TYPE_ATTACK

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
        if not direction_is_valid(direction):
            return {
                'from': self.coordinate,
                'to': self.coordinate,
                'error': 'Direction {} is invalid'.format(direction),
            }
        delta_x, delta_y = direction
        latitude = self.coordinate.latitude + delta_x
        longitude = self.coordinate.longitude + delta_y
        desired_coordinate = Coordinate(latitude, longitude)

        if not coord_in_arena(desired_coordinate, self.arena):
            return {
                'from': self.coordinate,
                'to': desired_coordinate,
                'error': 'Invalid position ({}, {})'.format(latitude, longitude),
            }

        destination_tile = self.arena[desired_coordinate]

        if not destination_tile.reachable:
            return {
                'from': self.coordinate,
                'to': desired_coordinate,
                'error': 'Blocked position ({}, {})'.format(latitude, longitude),
            }


        if destination_tile.hq_for(self.player_id) and not destination_tile.empty:
            return {
                'from': self.coordinate,
                'to': desired_coordinate,
                'error': 'You can place only one unit on your base',
            }

        if not self.can_invade(destination_tile):
            return {
                'from': self.coordinate,
                'to': desired_coordinate,
                'error': 'All occupiers must be of the same team',
            }

        # Move from current position to next one
        self.arena.move(self, self.coordinate, desired_coordinate)
        origin = self.coordinate
        self.coordinate = desired_coordinate
        return {
            'from': origin,
            'to': self.coordinate,
            'error': '',
        }

    def can_invade(self, tile):
        """It is possible to invade a tile if
        * it is empty
        * all units in it are from the same team
        * it is the enemy's headquarter and it is empty
        """
        return self._all_units_are_mine(tile) or self._enemy_headquarter_alone(tile)

    def _all_units_are_mine(self, tile):
        """@return :bool: indicating if all the units in <tile> are from
        <self>."""
        return all(unit.player_id == self.player_id for unit in tile.items)

    def _enemy_headquarter_alone(self, tile):
        """@return :bool: indicating if the <tile> is the enemy HeadQuarter,
        and is alone."""
        enemy_units = [u for u in tile.items if u.player_id != self.player_id]
        return len(enemy_units) == 1 and enemy_units[0].type == UNIT_TYPE_HQ
