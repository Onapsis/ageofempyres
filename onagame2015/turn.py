from itertools import groupby


class GameTurn(object):
    """Abstract the actions that take place during a turn, and when it
    finishes, return a summarized status of what happened so the engine can
    trace it.
    """
    def __init__(self, arena, turn_number):
        self.arena = arena
        self.trace = []
        self.history = []
        self.turn_number = turn_number

    def evaluate_bot_action(self, bot_response):
        """Get the action performed by the bot, and update
        the temporary status of it."""
        if not bot_response.get('error') and bot_response.has_key('action_type'):
            self.history.append(bot_response)

    def summarize_moves(self, actions):
        key_func = lambda x: (x['player'], x['from'], x['to'])
        for (player, origin, end), movements in groupby(sorted(actions, key=key_func), key_func):
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
                'turn_number': self.turn_number,
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
                    "dice": attack['attacker_dice'],
                    "remaining_units": attack['attacker_units'],
                    "lost_units": attack['attacker_loses']
                },
                "to": {
                    "player": attack['defender_player'],
                    "tile": {"x": def_cord.longitude, "y": def_cord.latitude},
                    "dice": attack['defender_dice'],
                    "remaining_units": attack['defender_units'],
                    "lost_units": attack['defender_loses']
                },
                'turn_number': self.turn_number,
            })

    def summarize_actions(self):
        for key, actions in groupby(self.history, key=lambda x: x['action_type']):
            actions = list(actions)
            if key == 'MOVE':
                self.summarize_moves(actions)
            elif key == 'ATTACK':
                self.summarize_attacks(actions)

    def end_turn_status(self):
        self.summarize_actions()
        return self.trace
