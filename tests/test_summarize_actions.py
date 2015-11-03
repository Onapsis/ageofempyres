import pytest
from onagame2015.turn import GameTurn
from onagame2015.lib import Coordinate


def test_empty_list_will_return_an_empty_list():
    # Setup
    turn = GameTurn(None)
    turn.history = []
    expected_result = []

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    assert list(trace) == expected_result

def test_all_moves():
    # Setup
    turn = GameTurn(None)
    turn.history = [
        {'from': Coordinate(longitude=1, latitude=0), 'to': Coordinate(longitude=1, latitude=1),
         'remain_in_source': 1, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'from': Coordinate(longitude=1, latitude=0), 'to': Coordinate(longitude=0, latitude=1),
         'remain_in_source': 0, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'from': Coordinate(longitude=1, latitude=1), 'to': Coordinate(longitude=0, latitude=1),
         'remain_in_source': 3, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'from': Coordinate(longitude=1, latitude=1), 'to': Coordinate(longitude=0, latitude=1),
         'remain_in_source': 2, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'from': Coordinate(longitude=1, latitude=0), 'to': Coordinate(longitude=1, latitude=1),
         'remain_in_source': 0, 'player': '1', 'action_type': 'MOVE', 'error': None},
    ]
    expected_result = [
        (0, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 0},
                'remaining_units': 0,
            },
            'to': {
                'tile': {'x': 1, 'y': 1},
                'units': 2
            }
        }),
        (1, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 0, 'y': 1},
                'remaining_units': 0,
            },
            'to': {
                'tile': {'x': 1, 'y': 0},
                'units': 1
            }
        }),
        (2, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 1},
                'remaining_units': 2,
            },
            'to': {
                'tile': {'x': 1, 'y': 0},
                'units': 2
            }
        }),
    ]

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    import pprint

    l = list(trace)
    pprint.pprint(l)
    assert l == expected_result
