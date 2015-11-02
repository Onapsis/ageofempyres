from collections import namedtuple
Coordinate = namedtuple('Coordinate', 'latitude longitude')

FREE = 0
UNAVAILABLE_TILE = 1
FOG_CONSTANT = "F"
VISIBILITY_DISTANCE = 3
STARTS_WITH_N_UNITS = 1
ADD_NEW_UNITS_ROUND = 2

AVAILABLE_MOVEMENTS = (Coordinate(0, 1),
                       Coordinate(0, -1),
                       Coordinate(1, 0),
                       Coordinate(-1, 0)
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
