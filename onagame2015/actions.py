import random
from onagame2015.validations import coord_in_arena
from onagame2015.lib import Coordinate


def toss_dice(number_of_dice):
    for _ in range(number_of_dice):
        yield random.randint(1, 6)


class BaseBotAction(object):
    ACTION_NAME = ''

    def __init__(self, bot):
        self.calling_bog = bot
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
            'from': <attack_from>,
            'to': <attack_to>,
        }
        Validate <attack_{from,to}> are contiguous cells in the arena.
        If possible, run the attack, and update the units in each tile
        according to the result.
        """
        # TODO: When a soldier attack, the enemy must be front of him and it must be from other team
        attacker_coord = action['from']
        defender_coord = action['to']
        self._run_attack_validations(
            arena=arena,
            tile_from=attacker_coord,
            tile_to=defender_coord,
        )
        attacker_tile = arena.get_content_on_tile(attacker_coord)
        defender_tile = arena.get_content_on_tile(defender_coord)
        attack_result = self._launch_attack(
            attacker_tile=attacker_tile,
            defender_tile=defender_tile,
        )

    def _launch_attack(self, attacker_tile, defender_tile):
        """Run the attack on the tiles, by using the units in each one
        @return: dict indicating how many unit loses every team
        """
        attacker_dice = len(attacker_dice.items)
        defender_dice = len(defender_dice.items)
        play = lambda n_dice: sorted(toss_dice(n_dice), reverse=True)
        partial_result = dict(attacker_loses=0, defender_loses=0)
        for attacker, defender in zip(play(attacker_dice), play(defender_dice)):
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
        self._contiguous_tiles(tile_from=tile_from, tile_to=tile_to)
        self._oposite_bands(tile_from=tile_from, tile_to=tile_to)

    def _tiles_in_arena(self, tiles, arena):
        if not all(coord_in_arena(t, arena) for t in tiles):
            raise RuntimeError("Invalid coordinates")

    def _contiguous_tiles(self, tile_from, tile_to):
        pass # TODO

    def _oposite_bands(self, tile_from, tile_to):
        """Validate that both tiles have units of different teams."""
        pass # TODO


class MoveAction(BaseBotAction):
    ACTION_NAME = 'MOVE'

    def execute(self, arena, action):
        """@return :dict: with
        {
          'action_type': 'MOVE',
          'from': <coord> for the origin,
          'to: <coord> of destiny,
          'error': <empty> if OK or msg error description
        }
        """
        action_resutl = {'action_type': 'MOVE'}
        unit = arena.get_unit(action['unit_id'])
        action_resutl.update(unit.move(action['direction']))
        return action_resutl
