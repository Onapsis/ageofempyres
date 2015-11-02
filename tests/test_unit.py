from random import randint

import pytest

from onagame2015.lib import Coordinate
from onagame2015.units import AttackUnit
from onagame2015.arena import ArenaGrid, TileContainer


def test_attack_unit_move_invalid_input(random_arena):
    attack_unit = AttackUnit(Coordinate(0, 0), 1, random_arena)

    result = attack_unit.move('UP')

    assert result.get('error') and 'invalid' in result.get('error')


def test_attack_unit_move_coord_not_in_arena(random_arena):
    initial_coordinate = Coordinate(0, 0)
    attack_unit = AttackUnit(initial_coordinate, 1, random_arena)

    result = attack_unit.move((randint(101, 120), randint(101, 120)))

    assert result.get('error') and 'invalid' in result.get('error')
    assert attack_unit.coordinate == initial_coordinate
