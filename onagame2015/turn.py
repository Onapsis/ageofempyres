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
        self._actions = {
            'ATTACK': self._update_attack,
            'MOVE': self._update_move,
        }

    def evaluate_bot_action(self, bot_response):
        """Get the action performed by the bot, and update
        the temporary status of it."""
        self._actions[bot_response['action_type']](bot_response)

    def _update_move(self, bot_response):
        """Update a movement made by the bot. Keep track of how many units
        entered and left each coordinate in the arena.
        """
        unique_transition = (bot_response['from'], bot_response['to'])
        origin, end = unique_transition
        self._units_in[origin] = self.arena.number_of_units_in_tile(origin) - 1
        self._units_in[end] = self.arena.number_of_units_in_tile(end) + 1
        self._transitions[unique_transition] = 1

    def summarize_moves(self):
        base = {
            'action': 'MOVE_UNITS',
            'player': '',
            'from': {},
            'to': {},
        }
        for (origin, end), _ in self._transitions.iteritems():
            action = {}
            action.update(base)
            action['from'] = {
                'tile': {'x': origin.latitude, 'y': origin.longitude},
                'remaining_units': self._units_in[origin],
            }
            action['to'] = {
                'tile': {'x': end.latitude, 'y': end.longitude},
                'units': self._units_in[end],
            }
            self.trace.append(action)

    def summarize_attacks(self):
        pass

    def _update_attack(self, bot_response):
        pass

    def end_turn_status(self):
        self.summarize_moves()
        self.summarize_attacks()
        return enumerate(self.trace)
