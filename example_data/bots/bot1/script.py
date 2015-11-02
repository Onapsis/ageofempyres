# import random
from basebot import BaseBot


class Bot(BaseBot):

    def __init__(self):
        super(Bot, self).__init__()
        self.actions = []
        self.player_id = None
        self._reset_units()

    def move_unit(self, unit_id, direction):
        self.actions.append({
            'action_type': 'MOVE',
            'unit_id': unit_id,
            'direction': direction,
        })

    def attack_tile(self, attack_from, attack_to):
        self.actions.append({
            'action_type': 'ATTACK',
            'from': attack_from,
            'to': attack_to
        })

    def _reset_units(self):
        self.hq_xy = []
        self.my_army = []
        self.enemies = []

    def get_units_location(self, game_map):
        for r_count, row in enumerate(game_map):
            for c_count, tile in enumerate(row):
                if 'HQ' in tile:
                    # Get our HQ location
                    self.hq_xy = [r_count, c_count]
                if 'U:' in tile:
                    # There are units in this tile
                    for unit in tile.split(','):
                        unit_id = unit.split(':')[-1]
                        if 'U:' not in unit:
                            continue
                        if 'U:%s' % self.player_id in unit:
                            # friendly unit
                            self.my_army.append(([r_count, c_count, unit_id]))
                        else:
                            # enemy unit!
                            self.enemies.append(([r_count, c_count]))

    def attack_if_its_possible(self, attacker_position, delta_target):
        """Try to attack some tile

        :param attacker_position: Attacker position
        :param delta_target: Delta from attacker position where should be the target
        :return: True if attack could be done, False in other case
        """
        target_position = attacker_position
        target_position[0] += delta_target[0]
        target_position[1] += delta_target[1]
        if target_position in self.enemies:
            self.attack_tile(attacker_position, target_position)

            return True

        return False

    def on_turn(self, data_dict):
        self._reset_units()
        self.actions = []
        self.player_id = data_dict['player_num']

        self.get_units_location(data_dict['map'])

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.move_units(directions, len(data_dict['map']))
        #self.attack_with_units(directions)

        return {'ACTIONS': self.actions}

    def attack_with_units(self, directions):
        # All units must try to attack
        for attacker_position in {(x, y) for x, y, unit_id in self.my_army}:
            for d in directions:
                if self.attack_if_its_possible(attacker_position, d):
                    break

    def move_units(self, directions, map_size):
        # Try to move all attackers in random direction
        for y, x, unit_id in self.my_army:
            for direction in directions:
                if self.is_possible_to_move_to_direction(map_size, x, y, direction):
                    self.move_unit(unit_id, direction)
                    break

    def is_possible_to_move_to_direction(self, map_size, x, y, direction):
        return 0 <= x + direction[0] < map_size and 0 <= y + direction[1] < map_size
