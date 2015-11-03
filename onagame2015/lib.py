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


class GameStages(object):
    INITIAL = 'initial'
    TURNS = 'turns'
    FINAL = 'final'

    stages = (INITIAL, TURNS, FINAL)


class InvalidBotOutput(Exception):
    reason = u'Invalid output'


class BotTimeoutException(Exception):
    reason = u'Timeout'


class GameOverException(Exception):
    pass


class GameBaseObject(object):

    def __json__(self):
        """To be implemented by each object that wants to participate on the
        game result."""
        return {}
