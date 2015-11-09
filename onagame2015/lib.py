from collections import namedtuple
Coordinate = namedtuple('Coordinate', 'latitude longitude')

FREE = 0
UNAVAILABLE_TILE = 1
FOG_CONSTANT = "F"
VISIBILITY_DISTANCE = 3
STARTS_WITH_N_UNITS = 1
ADD_NEW_UNITS_ROUND = 2


SOUTH_COORDINATE = Coordinate(0, 1)
NORTH_COORDINATE = Coordinate(0, -1)
EAST_COORDINATE = Coordinate(1, 0)
WEST_COORDINATE = Coordinate(-1, 0)
SOUTH_EAST_COORDINATE = Coordinate(EAST_COORDINATE.latitude, SOUTH_COORDINATE.longitude)
SOUTH_WEST_COORDINATE = Coordinate(WEST_COORDINATE.latitude, SOUTH_COORDINATE.longitude)
NORTH_EAST_COORDINATE = Coordinate(EAST_COORDINATE.latitude, NORTH_COORDINATE.longitude)
NORTH_WEST_COORDINATE = Coordinate(WEST_COORDINATE.latitude, NORTH_COORDINATE.longitude)

AVAILABLE_MOVEMENTS = (
    SOUTH_COORDINATE,
    NORTH_COORDINATE,
    EAST_COORDINATE,
    WEST_COORDINATE,
    SOUTH_EAST_COORDINATE,
    SOUTH_WEST_COORDINATE,
    NORTH_EAST_COORDINATE,
    NORTH_WEST_COORDINATE,
)

BOT_COLORS = ("0x000077", "0xFF0000")

class GameStages(object):
    INITIAL = 'initial'
    TURNS = 'actions'
    FINAL = 'final'

    stages = (INITIAL, TURNS, FINAL)


class InvalidBotOutput(Exception):
    reason = u'Invalid output'


class BotTimeoutException(Exception):
    reason = u'Timeout'


class GameOverException(Exception):
    reason = u'Game Over'


class GameBaseObject(object):

    def __json__(self):
        """To be implemented by each object that wants to participate on the
        game result."""
        return {}


def distance(point1, point2):
    """Return the calculated distance between the points.
    Manhattan distance.
    """
    x0, y0 = point1
    x1, y1 = point2
    return abs(x1 - x0) + abs(y1 - y0)


def farthest_from_point(point, list_of_points):
    """Given a <point>, return one of the <list_of_points> that is the most far
    away as possible from the original <point>."""
    return max(list_of_points, key=lambda p: distance(point, p))
