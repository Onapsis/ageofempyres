from collections import namedtuple
Coordinate = namedtuple('Coordinate', 'x y')

FREE = 0
UNAVAILABLE_TILE = 1
FOG_CONSTANT = "F"
VISIBILITY_DISTANCE = 3
STARTS_WITH_N_UNITS = 5

AVAILABLE_MOVEMENTS = ((0, 1), (0, -1), (1, 0), (-1, 0))


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
