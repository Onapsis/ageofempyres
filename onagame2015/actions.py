import random
from onagame2015.validations import (
    coord_in_arena,
    arg_is_valid_tuple,
)
from onagame2015.lib import Coordinate


def toss_dice(number_of_dice):
    for _ in range(number_of_dice):
        yield random.randint(1, 6)


class BaseBotAction(object):
    ACTION_NAME = ''

    def __init__(self, bot):
        self.calling_bot = bot
        self.result = ''

    def action_result(self):
        return {
            'result': self.result,
        }

    def execute(self, arena, action):
        """Return a dict, indicating what was done
        Implemented by the subclass
        {
         'action_type': -> 'ATTACK' | 'MOVE',
         ....
        }
        """
        raise NotImplementedError


class AttackAction(BaseBotAction):
    ACTION_NAME = 'ATTACK'

    def execute(self, arena, action):
        """Attack from one tile to another
        :action: <dict> with {
            'action_type': 'ATTACK',
            'from': <coord> attack from,
            'to': <coord> attack to,
        }
        Validate <attack_{from,to}> are adjacent cells in the arena.
        If possible, run the attack, and update the units in each tile
        according to the result.
        @return
        {
          'action_type': 'ATTACK',
          'attacker_coord': <coord_attack_from>,
          'defender_coord': <coord_attack_to>,
          'defender_units': <n>,
          'attacker_units': <m>,
        }
        """
        if not arg_is_valid_tuple(action['from']) or not arg_is_valid_tuple(action['to']):
            raise RuntimeError("Invalid tuple")

        # Because it's a list of lists, the user will parse the matrix,
        #   first through longitude and then through latitude
        #   The coordinates will come reversed
        attacker_coord = Coordinate(latitude=action['from'][1], longitude=action['from'][0])
        defender_coord = Coordinate(latitude=action['to'][1], longitude=action['to'][0])
        self._run_attack_validations(
            arena=arena,
            tile_from=attacker_coord,
            tile_to=defender_coord,
        )
        attacker_tile = arena.get_tile_content(attacker_coord)
        defender_tile = arena.get_tile_content(defender_coord)
        attack_result = self._launch_attack(
            attacker_tile=attacker_tile,
            defender_tile=defender_tile,
        )
        result = {
            'action_type': 'ATTACK',
            'attacker_coord': attacker_coord,
            'defender_coord': defender_coord,
            'defender_units': arena.number_of_units_in_tile(defender_coord) - attack_result['defender_loses'],
            'attacker_units': arena.number_of_units_in_tile(attacker_coord) - attack_result['attacker_loses'],
            'attacker_player': arena.whos_in_tile(attacker_coord),
            'defender_player': arena.whos_in_tile(defender_coord),
        }
        result.update(attack_result)
        arena.synchronize_attack_results(attack_result)
        return result

    def _launch_attack(self, attacker_tile, defender_tile):
        """Run the attack on the tiles, by using the units in each one
        @return: dict indicating how many unit loses every team
        {
            'attacker_loses': <n> :int:,
            'defender_loses': <m> :int:,
            'attacker_dice': [x0, x1,....],
            'defender_dice': [y0, y1,....],
        }
        """
        attacker_n_dice = len(attacker_tile.items) - 1
        defender_n_dice = len(defender_tile.items)
        play = lambda n_dice: sorted(toss_dice(n_dice), reverse=True)
        attacker_dice = play(attacker_n_dice)
        defender_dice = play(defender_n_dice)
        partial_result = {
            'attacker_loses': 0,
            'defender_loses': 0,
            'attacker_dice': attacker_dice,
            'defender_dice': defender_dice,
        }
        for attacker, defender in zip(attacker_dice, defender_dice):
            if attacker <= defender:
                partial_result['attacker_loses'] += 1
            else:
                partial_result['defender_loses'] += 1
        return partial_result

    def _run_attack_validations(self, arena, tile_from, tile_to):
        """Run a series of validations to assess if is possible to perform an
        attack with the given pair of coordinates."""
        self._tiles_in_arena(
            tiles=(Coordinate(*point) for point in (tile_to, tile_from)),
            arena=arena)
        self._contiguous_tiles(source_coord=tile_from, target_coord=tile_to)
        self._oposite_bands(arena=arena, attacker_coord=tile_from, defender_coord=tile_to)

    def _tiles_in_arena(self, tiles, arena):
        if not all(coord_in_arena(t, arena) for t in tiles):
            raise RuntimeError("Invalid coordinates")

    def _contiguous_tiles(self, source_coord, target_coord):
        delta_latitude = abs(source_coord.latitude - target_coord.latitude)
        delta_longitude = abs(source_coord.longitude - target_coord.longitude)
        try:
            assert 1 <= delta_latitude + delta_longitude <= 2
        except AssertionError:
            raise RuntimeError("Invalid attack range")

    def _oposite_bands(self, arena, attacker_coord, defender_coord):
        """Validate that both tiles have units of different teams."""
        attacker_tile = arena.get_tile_content(attacker_coord)
        defender_tile = arena.get_tile_content(defender_coord)
        try:
            team_1 = next(unit.player_id for unit in attacker_tile.items)
            team_2 = next(unit.player_id for unit in defender_tile.items)
            assert team_1 != team_2, "Friendly fire!"
        except AssertionError as e:
            raise RuntimeError(str(e))
        except StopIteration:
            raise RuntimeError("One of the tiles is empty")


class MoveAction(BaseBotAction):
    ACTION_NAME = 'MOVE'

    def execute(self, arena, action):
        """@return :dict: with
        {
          'action_type': 'MOVE',
          'from': <coord> for the origin,
          'to: <coord> of destiny,
          'remain_in_source': <n>,
          'error': <empty> if OK or msg error description,
          'player': <player_that_moved>,
        }
        """
        action_result = {'action_type': 'MOVE'}
        unit = arena.get_unit(action['unit_id'])
        action_result.update(unit.move(action['direction']))
        action_result['remain_in_source'] = arena.number_of_units_in_tile(action_result['from'])
        action_result['player'] = arena.whos_in_tile(action_result['from'])
        return action_result
