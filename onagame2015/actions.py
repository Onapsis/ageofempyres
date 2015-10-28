from onagame2015.validations import coord_in_arena
from onagame2015.engine import Coordinate


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
        pass


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
        If possible, run the attack, and update the units in each tail
        according to the result.
        """
        # TODO: When a soldier attack, the enemy must be front of him and it must be from other team
        self._run_attack_validations(
            arena=arena,
            tail_from=action['from'],
            tail_to=action['to'])

    def _run_attack_validations(self, arena, tail_from, tail_to):
        """Run a series of validations to assess if is possible to perform an
        attack with the given pair of coordinates."""
        self._tails_in_arena(
            tails=(Coordinate(*point) for point in (tail_to, tail_from)),
            arena=arena)
        self._contiguous_tails(tail_from, tail_to)
        self._oposite_bands(tail_from, tail_to)

    def _tails_in_arena(self, tails, arena):
        if not all(coord_in_arena(t, arena) for t in tails):
            raise RuntimeError("Invalid coordinates")

    def _contiguous_tails(self, tail_from, tail_to):
        pass # TODO

    def _oposite_bands(self, tail_from, tail_to):
        """Validate that both tails have units of different teams."""
        pass # TODO


class MoveAction(BaseBotAction):
    ACTION_NAME = 'MOVE'

    def execute(self, arena, action):
        unit = arena.get_unit(action['unit_id'])
        if unit:
            try:
                unit.move(action['direction'])
            except Exception as e:
                return "Exceptions: '{}' Unit: {}".format(e, unit)

        return unit
