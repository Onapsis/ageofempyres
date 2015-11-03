from itertools import groupby
from collections import defaultdict


def group_chunks_by_type(chunks, action):
    if not action['error']:
        if chunks[-1]['action_type'] == action['action_type']:
            chunks[-1]['actions'].append(action)
        else:
            chunks.append({'action_type': action['action_type'], 'actions': [action]})

    return chunks


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
        self.history = []

    def evaluate_bot_action(self, bot_response):
        """Get the action performed by the bot, and update
        the temporary status of it."""
        self.history.append(bot_response)

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
                    "remaining_units": min(x['remain_in_source'] for x in movements)
                },
                'to': {
                    "tile": {"x": end.longitude, "y": end.latitude},
                    "units": len(movements)
                },
            }

            self.trace.append(summary)

    def summarize_attacks(self, actions):
        """ Gets a list of actions like:
        {
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
        }

        and append into self.trace list actions like:

        {
            "action": "ATTACK",
            "player": "player1",
            "from": {
                "tile": { "x": 4, "y": 3 },
                "dice": [1, 3, 3],
                "remaining_units": 2,
                "lost_units": 1
            },
            "to": {
                "player": "player2",
                "tile": { "x": 5, "y": 3 },
                "dice": [3, 2],
                "remaining_units": 1,
                "lost_units": 1
            }
        }
        """
        for attack in actions:
            att_cord = attack['attacker_coord']
            def_cord = attack['defender_coord']
            self.trace.append({
                "action": "ATTACK",
                "player": attack['attacker_player'],
                "from": {
                    "tile": {"x": att_cord.longitude, "y": att_cord.latitude},
                    # "units": attack['attacker_units'] + attack['attacker_loses'],
                    "dice": attack['attacker_dice'],
                    "remaining_units": attack['attacker_units'],
                    "lost_units": attack['attacker_loses']
                },
                "to": {
                    "player": attack['defender_player'],
                    "tile": {"x": def_cord.longitude, "y": def_cord.latitude},
                    # "units": attack['defender_units'] + attack['defender_loses'],
                    "dice": attack['defender_dice'],
                    "remaining_units": attack['defender_units'],
                    "lost_units": attack['defender_loses']
                },
            })

    def _update_attack(self, bot_response):
        pass

    def summarize_actions(self):
        if self.history:
            action = self.history.pop(0)
            initial = [{'action_type': action['action_type'], 'actions': [action]}]
            chunks = reduce(group_chunks_by_type, self.history, initial)

            for chunk in chunks:
                if chunk['action_type'] == 'MOVE':
                    self.summarize_moves(chunk['actions'])
                elif chunk['action_type'] == 'ATTACK':
                    self.summarize_attacks(chunk['actions'])

    def end_turn_status(self):
        self.summarize_actions()
        return enumerate(self.trace)