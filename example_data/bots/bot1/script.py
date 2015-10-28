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
            'direction': direction
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
        self._reset_units()
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
        self.player_id = data_dict['player_num']
        self.actions = []
        self.my_army = []
        self.enemies = []
        map = data_dict['map']
        self.get_units_location(map)
        print "HQ_XY: ", self.hq_xy
        print "UNITS LOCATION: ", self.my_army
        print "ENEMY UNITS: ", self.enemies

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        # random.shuffle(self.my_army)
        self.move_units(directions)
        # self.attack_with_units(directions)

        return {'ACTIONS': self.actions}

    def attack_with_units(self, directions):
        # All units must try to attack
        for attacker_position in {u[:-1] for u in self.my_army}:
            # random.shuffle(directions)
            for d in directions:
                if self.attack_if_its_possible(attacker_position, d):
                    break

    def move_units(self, directions):
        # Try to move all attackers in random direction
        for unit_id in (x[-1] for x in self.my_army):
            # directions = random.shuffle(directions)
            for d in directions:
                self.move_unit(unit_id, d)
                break
