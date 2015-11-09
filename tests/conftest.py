from random import randint

import pytest

from onagame2015.arena import ArenaGrid
from onagame2015.maploader import GameMap


@pytest.fixture(scope='function')
def random_arena():
    return ArenaGrid(GameMap.create_empty_map(
        width=randint(10, 100),
        height=randint(10, 100))
    )
