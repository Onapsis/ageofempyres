from random import randint

import pytest

from onagame2015.arena import ArenaGrid


@pytest.fixture(scope='function')
def random_arena():
    return ArenaGrid(randint(1, 100), randint(1, 100))
