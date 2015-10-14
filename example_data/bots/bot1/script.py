from basebot import BaseBot


class Bot(BaseBot):

    def __init__(self):
        self.player_num = None
        self.hq_xy = []
        self.units_xy = []
        self.enemies = []
        self.actions = []

    def move_unit(self, unit_from, unit_to):
        pass

    def get_units_location(self, map):
        self.hq_xy = []
        self.units_xy = []
        self.enemies = []
        r_count = 0
        for r in map:
            c_count = 0
            for c in r:
                if 'HQ' in c:
                    # Get our HQ location
                    self.hq_xy = [r_count, c_count]
                if 'U:' in c:
                    # There are units in this tile
                    for unit in c.split(','):
                        if 'U:' not in unit:
                            continue
                        if 'U:%s' % self.player_num in unit:
                            # friendly unit
                            self.units_xy.append(([r_count, c_count]))
                        else:
                            # enemy unit!
                            self.enemies.append(([r_count, c_count]))
                c_count += 1
            r_count += 1

    def on_turn(self, data_dict):
        self.player_num = data_dict['player_num']
        map = data_dict['map']
        self.get_units_location(map)
        print "HQ_XY: ", self.hq_xy
        print "UNITS LOCATION: ", self.units_xy
        print "ENEMY UNITS: ", self.enemies
        self.move_unit(self.units_xy[0])
        return {'ACTIONS': self.actions}