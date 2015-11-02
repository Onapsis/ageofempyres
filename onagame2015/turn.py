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
        #self._units_in[origin] = self.arena.units_in(origin) - 1
        #self._units_in[end] = self.arena.units_in(end) + 1

    def _update_attack(self, bot_response):
        pass

    def end_turn_status(self):
        return {}
