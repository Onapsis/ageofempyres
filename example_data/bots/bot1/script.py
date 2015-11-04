from gamebot import GameBot
from gamebot import InvalidActionException


class Bot(GameBot):

    def play(self, player_id, game_map):
        my_units = []
        for tile in game_map.itervalues():
            for unit in tile.units:
                for direction in self.DIRECTIONS:
                    try:
                        self.move(unit, direction)
                    except:
                        continue
                    else:
                        break
                try:
                    self.attack(tile+self.N, self.W)
                except InvalidActionException:
                    pass

