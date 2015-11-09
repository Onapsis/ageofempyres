from gamebot import GameBot
from gamebot import InvalidActionException


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


def shuffled(data):
    data_copy = data[:]
    for _ in xrange(0, len(data)):
        yield data_copy.pop(randint(0, len(data_copy)))


class Bot(GameBot):
    DIRECTIONS = [GameBot.N, GameBot.E, GameBot.S, GameBot.W]

    def __init__(self):

        self.visited = {}
        self.unit_directions = {}

    def play(self, player_id, game_map):
        for tile in game_map.itervalues():
            for unit in tile.units:
                try:
                    elegible = list(self.elegible_directions(unit))
                    direction = self.unit_directions.get(unit.unit_id, choice(elegible))
                    if not direction or direction not in elegible:
                        direction = choice(elegible)

                    self.move(unit, direction)
                    self.unit_directions[unit.unit_id] = direction

                except InvalidActionException as e:
                    del(self.unit_directions[unit.unit_id])
                    print e

    def turn_left(self, direction):
        return self.DIRECTIONS[(self.DIRECTIONS.index(direction) - 1) % len(self.DIRECTIONS)]

    def turn_right(self, direction):
        index = (self.DIRECTIONS.index(direction) + 1) % len(self.DIRECTIONS)
        return self.DIRECTIONS[index]

    def not_visited_directions(self, unit):
        visited = self.visited.setdefault(unit.unit_id, set())
        for direction in self.elegible_directions(unit):
            if (direction + unit).as_tuple() not in visited:
                yield direction

    def elegible_directions(self, unit):
        for direction in self.DIRECTIONS:
            target = direction + unit
            try:
                self.validate_target(target)
                if not self.game_map[target.as_tuple()].enemies_count:
                    yield direction
            except InvalidActionException:
                pass
