import pprint
from onagame2015.turn import GameTurn
from onagame2015.lib import Coordinate


def print_differences(expected_result, target):
    for x, y in zip(target, expected_result):
        if x != y:
            print 'ERROR:'
            print 'What we expect:'
            pprint.pprint(y)
            print 'What we got:'
            pprint.pprint(x)


def test_empty_list_will_return_an_empty_list():
    # Setup
    turn = GameTurn(None)
    turn.history = []
    expected_result = []

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    assert list(trace) == expected_result

def test_all_moves_will_be_sorted_and_group_by_coordinates():
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
                'tile': {'x': 0, 'y': 1},
                'units': 1
            }
        }),
        (1, {
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
        (2, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 1},
                'remaining_units': 2,
            },
            'to': {
                'tile': {'x': 0, 'y': 1},
                'units': 2
            }
        }),
    ]

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    target = list(trace)
    print_differences(expected_result, target)
    assert target == expected_result


def test_attack_action_it_will_translate_as_is_expected():
    # Setup
    turn = GameTurn(None)
    turn.history = [
        {'action_type': 'ATTACK', 'attacker_coord': Coordinate(longitude=1, latitude=0),
         'defender_coord': Coordinate(longitude=1, latitude=1), 'defender_units': 1, 'attacker_units': 4,
         'attacker_loses': 1, 'defender_loses': 2, 'attacker_player': 'player_id_1',
         'defender_player': 'player_id_2', 'attacker_dice': [6, 6, 5, 4, 3], 'defender_dice': [6, 3, 2]}
    ]
    expected_result = [
        (0,
         {'action': 'ATTACK',
          'from': {'dice': [6, 6, 5, 4, 3],
                   'lost_units': 1,
                   'remaining_units': 4,
                   'tile': {'x': 1, 'y': 0}},
          'player': 'player_id_1',
          'to': {'dice': [6, 3, 2],
                 'lost_units': 2,
                 'player': 'player_id_2',
                 'remaining_units': 1,
                 'tile': {'x': 1, 'y': 1}}}
         )
    ]

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    target = list(trace)
    import pprint
    pprint.pprint(target)
    print_differences(expected_result, target)
    assert target == expected_result


def test_mixing_moves_and_attacks_it_will_group_moves_and_then_attacks():
    # Setup
    turn = GameTurn(None)
    turn.history = [
        {'from': Coordinate(longitude=1, latitude=0), 'to': Coordinate(longitude=1, latitude=1),
         'remain_in_source': 1, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'from': Coordinate(longitude=1, latitude=0), 'to': Coordinate(longitude=0, latitude=1),
         'remain_in_source': 0, 'player': '1', 'action_type': 'MOVE', 'error': None},
        {'action_type': 'ATTACK', 'attacker_coord': Coordinate(longitude=3, latitude=2),
         'defender_coord': Coordinate(longitude=3, latitude=3), 'defender_units': 1, 'attacker_units': 4,
         'attacker_loses': 1, 'defender_loses': 2, 'attacker_player': 'player_id_1',
         'defender_player': 'player_id_2', 'attacker_dice': [6, 6, 5, 4, 3], 'defender_dice': [6, 3, 2]},
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
                'tile': {'x': 0, 'y': 1},
                'units': 1
            }
        }),
        (1, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 0},
                'remaining_units': 1,
            },
            'to': {
                'tile': {'x': 1, 'y': 1},
                'units': 1
            }
        }),
        (2,
         {'action': 'ATTACK',
          'from': {'dice': [6, 6, 5, 4, 3],
                   'lost_units': 1,
                   'remaining_units': 4,
                   'tile': {'x': 3, 'y': 2}},
          'player': 'player_id_1',
          'to': {'dice': [6, 3, 2],
                 'lost_units': 2,
                 'player': 'player_id_2',
                 'remaining_units': 1,
                 'tile': {'x': 3, 'y': 3}}}
         ),
        (3, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 0},
                'remaining_units': 0,
            },
            'to': {
                'tile': {'x': 1, 'y': 1},
                'units': 1
            }
        }),
        (4, {
            'action': 'MOVE_UNITS',
            'player': '1',
            'from': {
                'tile': {'x': 1, 'y': 1},
                'remaining_units': 2,
            },
            'to': {
                'tile': {'x': 0, 'y': 1},
                'units': 2
            }
        }),
    ]

    # Exercise
    trace = turn.end_turn_status()

    # Verify
    target = list(trace)
    print_differences(expected_result, target)
    assert target == expected_result
