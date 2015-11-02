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
        If possible, run the attack, and update the units in each tail
        according to the result.
        """
        # TODO: When a soldier attack, the enemy must be front of him and it must be from other team
        attacker_coord = action['from']
        defender_coord = action['to']
        self._run_attack_validations(
            arena=arena,
            tail_from=attacker_coord,
            tail_to=defender_coord,
        )
        attacker_tail = arena[attacker_coord.x][attacker_coord.y]
        defender_tail = arena[defender_coord.x][defender_coord.y]
        attack_result = self._launch_attack(
            attacker_tail=attacker_tail,
            defender_tail=defender_tail,
        )

    def _launch_attack(self, attacker_tail, defender_tail):
        """Run the attack on the tails, by using the units in each one
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

    def _run_attack_validations(self, arena, tail_from, tail_to):
        """Run a series of validations to assess if is possible to perform an
        attack with the given pair of coordinates."""
        self._tails_in_arena(
            tails=(Coordinate(*point) for point in (tail_to, tail_from)),
            arena=arena)
        self._contiguous_tails(tail_from=tail_from, tail_to=tail_to)
        self._oposite_bands(tail_from=tail_from, tail_to=tail_to)

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
