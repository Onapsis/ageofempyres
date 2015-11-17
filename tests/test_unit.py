import pytest

from onagame2015.lib import Coordinate
from onagame2015.units import AttackUnit

VALID_MOVES = (
    Coordinate(1, 0), Coordinate(-1, 0),
    Coordinate(0, 1), Coordinate(0, -1),
)


INVALID_MOVES_FROM_00 = (Coordinate(-1, 0), Coordinate(0, -1))

INVALID_INPUTS = ('UP', 2334, 0.343, {'up', -1})


@pytest.mark.parametrize('invalid_input', INVALID_INPUTS)
def test_attack_unit_move_invalid_input(random_arena, invalid_input):
    initial_coordinate = Coordinate(0, 0)
    attack_unit = AttackUnit(initial_coordinate, 1, random_arena)

    result = attack_unit.move(invalid_input)

    assert result.get('error') and 'invalid' in result.get('error')
    assert attack_unit.coordinate == initial_coordinate


@pytest.mark.parametrize('invalid_move', INVALID_MOVES_FROM_00 + (999999, 123))
def test_attack_unit_move_out_of_arena(random_arena, invalid_move):
    initial_coordinate = Coordinate(0, 0)
    attack_unit = AttackUnit(initial_coordinate, 1, random_arena)

    result = attack_unit.move((99999, 99999))

    assert result.get('error') and 'invalid' in result.get('error')
    assert attack_unit.coordinate == initial_coordinate


@pytest.mark.parametrize('valid_move', VALID_MOVES)
def test_attack_unit_move(random_arena, valid_move):
    initial_coordinate = Coordinate(2, 2)
    attack_unit = AttackUnit(initial_coordinate, 1, random_arena)
    expected = Coordinate(
        initial_coordinate.latitude + valid_move.latitude,
        initial_coordinate.longitude + valid_move.longitude)

    result = attack_unit.move(valid_move)

    assert not result.get('error')
    assert attack_unit.coordinate != initial_coordinate
    assert attack_unit.coordinate == expected
    assert result['from'] == initial_coordinate
    assert result['to'] == expected


def test_attack_unit_cant_move_if_occupied(random_arena):
    initial_coordinate = Coordinate(1, 1)
    initial_enemy_coordinate = Coordinate(1, 2)
    attack_unit = AttackUnit(initial_coordinate, 1, random_arena)
    enemy_unit = AttackUnit(initial_enemy_coordinate, 2, random_arena)
    random_arena.set_content_on_tile(initial_coordinate, attack_unit)
    random_arena.set_content_on_tile(initial_enemy_coordinate, enemy_unit)

    result = attack_unit.move(Coordinate(0, 1))

    assert result['error']
    assert result['from'] == initial_coordinate
    assert result['to'] == initial_coordinate
