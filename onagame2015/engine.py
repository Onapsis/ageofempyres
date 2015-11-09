from onagame2015.actions import BaseBotAction, MoveAction
from onagame2015.arena import ArenaGrid
from onagame2015.lib import (ADD_NEW_UNITS_ROUND, STARTS_WITH_N_UNITS,
                             GameStages)
from onagame2015.maploader import load_map
from onagame2015.status import GameStatus
from onagame2015.turn import GameTurn
from turnboxed.gamecontroller import BaseGameController


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.game_status = GameStatus()
        self.arena = ArenaGrid(load_map('map_draft.json'), self.game_status)
        self.bots = bots
        self.rounds = 100
        self._actions = {cls.ACTION_NAME: cls for cls in BaseBotAction.__subclasses__()}
        self.deploy_players()
        self.current_round = 0

    def deploy_players(self):
        initial_status = {
            "map_source": "map_draft.json",
            "fog_range": 1,
            'players': [],
        }
        deployed_players = self.arena.deploy_players(self.bots)
        initial_status.update(deployed_players)
        self.game_status.add_game_stage(GameStages.INITIAL, initial_status)

    @property
    def json(self):
        return self.game_status.json

    def get_bot(self, bot_cookie):
        bot_name = self.players[bot_cookie]['player_id']
        try:
            return next(b for b in self.bots if b.username == bot_name)
        except StopIteration:
            raise RuntimeError("No bot named {}".format(bot_name))

    @staticmethod
    def _validate_actions(actions):
        """Check if actions follow all rules:
        # At least one movement must be done
        # Each soldier can move once
        #TODO: If a soldier attacks, he can't move.

        :param actions: list of actions
        :return: None, raise an Exception if some rule is broken
        """
        moved_units = []
        for action in actions:
            if action['action_type'] == MoveAction.ACTION_NAME:
                if action['unit_id'] in moved_units:
                    raise Exception('Error: Unit {unit_id} moved twice'.format(**action))

                moved_units.append(action['unit_id'])

        if not moved_units:
            raise Exception('At least one movement must be done')

    def _update_game_status(self):
        for new_status in self._game_turn.end_turn_status():
            self.game_status.update_turns(new_status)

    def _handle_bot_failure(self, bot, request):
        """Manage the case if one of the bots failed,
        in that case, stop the execution, and log accordingly.
        """
        if "EXCEPTION" in request:
            # bot failed in turn
            self.log_msg("Bot %s crashed: %s %s" % (bot.username,
                                                    request['EXCEPTION'],
                                                    request['TRACEBACK']))
            self.stop()
            return -1

    def inform_result(self, winner=None, reason=None):
        final_status = {
            'action': 'GAMEOVER',
            'reason': reason,
            'result': 'WIN' if winner else 'DRAW',
            'player': winner or '',
        }
        self.game_status.add_game_stage(GameStages.FINAL, final_status)

    def evaluate_turn(self, request, bot_cookie):
        """
        # Game logic here.
        @return: <int>
        """
        bot = self.get_bot(bot_cookie)
        opponent = [b for b in self.bots if bot.username != b.username][0]

        winner, reason = self.check_game_over(bot, opponent)
        if winner or reason:
            self.inform_result(winner=winner, reason=reason)
            return -1
        self._game_turn = GameTurn(arena=self.arena, turn_number=self.current_round)

        if self._handle_bot_failure(bot, request) == -1:
            self.inform_result(
                winner=opponent,
                reason="Bot {} crashed!!".format(bot.username)
            )
            return -1

        self.log_msg("GOT Action: %s" % request['MSG']['ACTIONS'])
        self._validate_actions(request['MSG']['ACTIONS'])

        for action in request['MSG']['ACTIONS']:
            bot_action_type = self._actions.get(action['action_type'], BaseBotAction)
            bot = self.get_bot(bot_cookie)
            result = bot_action_type(bot).execute(self.arena, action, opponent)
            self._game_turn.evaluate_bot_action(result)

        self._update_game_status()
        return 0

    def check_game_over(self, current_player, opponent):
        winner = None

        player_won, reason = current_player.has_won_game(opponent, self.arena)
        if player_won:
            winner = current_player.p_num
            return winner, reason

        opponent_won, reason = opponent.has_won_game(current_player, self.arena)
        if opponent_won:
            winner = opponent.p_num
            return winner, reason

        if self.current_round == self.rounds:
            if len(current_player.units) > len(opponent.units):
                winner = current_player
                reason = "Turns limit reached! Player {} has more units than Player {}".format(current_player.username, opponent.username)
            elif len(current_player.units) < len(opponent.units):
                winner = opponent
                reason = "Turns limit reached! Player {} has more units than Player {}".format(opponent.username, current_player.username)
            else:
                # No winner here
                reason = "Turns limit reached! Both players have the same amount of units!"
        return winner, reason

    def get_turn_data(self, bot_cookie):
        """Feedback
        :return: the data sent to the bot on each turn
        """
        bot = self.get_bot(bot_cookie)
        return {
            'map': self.arena.get_map_for_player(bot),
            'player_num': bot.p_num,
        }

