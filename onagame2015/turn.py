from itertools import groupby
from collections import defaultdict


class GameTurn(object):
    """Abstract the actions that take place during a turn, and when it
    finishes, return a summarized status of what happened so the engine can
    trace it.
    """
    def __init__(self, arena):
        self.arena = arena
        self._units_in = defaultdict(int)
        self._attacks = defaultdict(dict)
        self._transitions = {}
        self.trace = []
        self._actions = []

    def evaluate_bot_action(self, bot_response):
        """Get the action performed by the bot, and update
        the temporary status of it."""
        self._actions.append(bot_response)

    def _update_move(self, bot_response):
        """Update a movement made by the bot. Keep track of how many units
        entered and left each coordinate in the arena.
        """
        unique_transition = (bot_response['from'], bot_response['to'])
        origin, end = unique_transition
        self._units_in[origin] = self.arena.number_of_units_in_tile(origin) - 1
        self._units_in[end] = self.arena.number_of_units_in_tile(end) + 1
        self._transitions[unique_transition] = 1

    def summarize_moves(self, actions):
        for (player, origin, end), movements in groupby(actions, lambda x: (x['player'], x['from'], x['to'])):
            movements = list(movements)
            summary = {
                'action': 'MOVE_UNITS',
                'player': player,
                'from': {
                    "tile": {"x": origin.longitude, "y": origin.latitude},
                    "remaining_units": min(movements, key=lambda x: x['remain_in_source'])
                },
                'to': {
                    "tile": {"x": origin.longitude, "y": origin.latitude},
                    "units": len(movements)
                },
            }
            self.trace.append(summary)

    def summarize_attacks(self, actions):
        """
            'action_type': 'ATTACK',
            'attacker_coord': attacker_coord,
            'defender_coord': defender_coord,
            'defender_units': arena.number_of_units_in_tile(defender_coord) - attack_result['defender_loses'],
            'attacker_units': arena.number_of_units_in_tile(attacker_coord) - attack_result['attacker_loses'],
            'attacker_loses': <n> :int:,
            'defender_loses': <m> :int:,
            'attacker_player': player_id,
            'defender_player': player_id,
            'attacker_dice': [x0, x1,....],
            'defender_dice': [y0, y1,....],

        :param actions:
        :return:
        """
        pass

    def summarize_adds(self, actions):
        pass

    def _update_attack(self, bot_response):
        pass

    def summarize_actions(self):
        chunks = []
        chunk_by_type = {
            'type': self._actions[0]['type'],
            'actions': []
        }

        for action in self._actions:
            if action['action_type'] == chunk_by_type['action_type']:
                chunk_by_type['actions'].append(action)
            else:
                chunks.append(chunk_by_type)

        for chunk in chunks:
            if chunk['action_type'] == 'MOVE':
                self.summarize_moves(chunk['actions'])
            elif chunk['action_type'] == 'ATTACK':
                self.summarize_attacks(chunk['actions'])
            elif chunk['action_type'] == 'ADD':
                self.summarize_adds(chunk['actions'])

    def end_turn_status(self):
        self.summarize_actions()
        return enumerate(self.trace)