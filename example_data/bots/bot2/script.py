from gamebot import GameBot, PointInMap

from functools import total_ordering
import itertools
import heapq

PATH_COST = 10


class Point(object):
    """Simple class to hold points, nametuple is not used because uses eval and
    is probably not enabled on the sandbox"""
    __slots__=('x', 'y',)

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def inside_grid(self, grid):
        return not (
            self.x < 0
            or self.y < 0
            or self.x >= len(grid[0])
            or self.y >= len(grid)
        )


DIRECTIONS = [Point(*t) for t in itertools.product((-1, 0, 1), repeat=2) if t != (0, 0)]


@total_ordering
class Cell(Point):
    """Represents a cell on the 2d grid"""
    __slots__ = ('reachable', 'end', '_parent', 'h', 'f', 'g')

    def __init__(self, x, y, reachable, end):
        super(Cell, self).__init__(x, y)
        self.reachable = reachable
        self._parent = None
        self.h = self._calculate_h(end)
        self.f = 0
        self.g = 0

    def _calculate_h(self, end):
        """Heuristic AKA manhatan distance"""
        return PATH_COST * (abs(self.x - end.x) + abs(self.y - end.y))

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        if isinstance(value, Cell):
            self._parent = value
            self.g = value.g + PATH_COST
            self.f = self.h + self.g

    def adjacent_cells(self, grid):
        for direction in DIRECTIONS:
            point = self + direction
            if point.inside_grid(grid):
                yield grid[point.y][point.x]

    def __eq__(self, other):
        return self.f == other.f

    def __lt__(self, other):
        return self.f < other.f

    def __repr__(self):
        return "Cell ({0.x}, {0.y}) h={0.h}  g={0.g} f={0.f}"


class AStarSolver():
    """Find a path in a 2d grid using dijkstra algorithm"""
    def __init__(self, grid, start, end):
        self.opened = []
        heapq.heapify(self.opened)
        self.closed = set()
        self.grid = []
        self._init_grid(grid, end)
        self.start = self.grid[start.y][start.x]
        self.end = self.grid[end.y][end.x]

    def _init_grid(self, grid, end):
        for y, row in enumerate(grid):
            _row = []
            for x, reachable in enumerate(row):
                _row.append(Cell(x, y, reachable, end))
            self.grid.append(_row)

    def path(self):
        path = [self.end]
        while path[-1].parent is not self.start:
            path.append(path[-1].parent)

        path.reverse()
        return path

    def process(self):
        heapq.heappush(self.opened, self.start)
        while len(self.opened):
            cell = heapq.heappop(self.opened)
            self.closed.add(cell)
            if cell is self.end:
                return self.path()

            for adjacent_cell in cell.adjacent_cells(self.grid):
                if adjacent_cell.reachable and adjacent_cell not in self.closed:
                    if adjacent_cell in self.opened:
                        if adjacent_cell.g > cell.g + PATH_COST:
                            adjacent_cell.parent = cell
                    else:
                        adjacent_cell.parent = cell
                        heapq.heappush(self.opened, adjacent_cell)


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

    def __init__(self):
        self.garrisoned_units = 1
        self.unit_destinations = {}
        self.current_turn = 0

    def play(self, player_id, game_map):
        try:
            if self.current_turn == 0:
                self.first_turn(player_id, game_map)

            self.discard_blocked_tiles(game_map)
            self.explore(game_map)
        finally:
            self.current_turn += 1

    def first_turn(self, player_id, game_map):
        self.explorers = [unit.unit_id for unit in
                                  self.iterate_over_units(self.game_map)][self.garrisoned_units:]

        self.unvisited = set(self.game_map.keys())

    def discard_blocked_tiles(self, game_map):
        for tile in game_map.itervalues():
            if not tile.reachable:
                self.unvisited.discard(tile.as_tuple())


    def iterate_over_units(self, game_map):
        for tile in game_map.itervalues():
            for unit in tile.units:
                yield unit

    def iterate_over_explorers(self, game_map):
        for explorer in self.iterate_over_units(game_map):
            if explorer.unit_id in self.explorers:
                yield explorer

    @property
    def width(self):
        return max(self.game_map.keys(), key=lambda p: p[0])[0] + 1

    @property
    def height(self):
        return max(self.game_map.keys(), key=lambda p: p[1])[1] + 1

    def random_coordinate(self):
        return PointInMap(*choice(list(self.unvisited)))

    def explore(self, game_map):
        for unit in self.iterate_over_explorers(game_map):
            self.unvisited.discard(unit.as_tuple())
            destination = self.unit_destinations.setdefault(unit.unit_id,
                                                            self.random_coordinate())
            if destination.x == unit.x and destination.y == unit.y:
                destination = self.random_coordinate()
                self.unit_destinations[unit.unit_id] = destination

            direction = self.calculate_shortest_path(unit, destination)
            direction_with_enemy = self.move_to_kill(game_map, unit)
            if direction_with_enemy is not None:
                direction = direction_with_enemy

            self.move(unit, direction)
            self.attack_if_possible(game_map, unit + direction)

    def calculate_shortest_path(self, start, destination):
        start = Point(start.x, start.y)
        end = Point(destination.x, destination.y)
        board = [
            [self.game_map[x, y].reachable for x in xrange(0, self.width)]
            for y in xrange(0, self.height)
        ]
        solver = AStarSolver(board, start, end)
        path = solver.process()
        next_cell = path[0]
        return PointInMap(next_cell.x - start.x, next_cell.y - start.y)

    def attack_if_possible(self, game_map, base_cell):
        for direction in self.DIRECTIONS:
            destination = base_cell + direction
            cell = game_map.get((destination).as_tuple())
            if cell is not None and cell.enemies_count:
                self.attack(base_cell, direction)
                break

    def move_to_kill(self, game_map, point):
        for direction in self.DIRECTIONS:
            destination = point + direction
            cell = game_map.get((destination).as_tuple())
            for d in self.DIRECTIONS:
                dest = destination + d
                cell = game_map.get((dest).as_tuple())
                if cell is not None and cell.enemies_count:
                    return direction