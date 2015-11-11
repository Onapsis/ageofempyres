from onagame2015.actions import BaseBotAction, MoveAction
from onagame2015.arena import ArenaGrid
from onagame2015.lib import (
    GameStages,
    VISIBILITY_DISTANCE,
)
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
            "fog_range": VISIBILITY_DISTANCE,
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

    def inform_game_result(self, winner=None, reason=None, rounds=0):
        """Register the final outcome for the game."""
        final_status = {
            'action': 'GAMEOVER',
            'reason': reason,
            'result': 'WIN' if winner else 'DRAW',
            'player': winner or '',
            'rounds': rounds,
            'total_rounds': self.rounds,
        }
        self.game_status.add_game_stage(GameStages.FINAL, final_status)
        return -1

    def evaluate_turn(self, request, bot_cookie):
        """
        # Game logic here.
        @return: <int>
        """
        bot = self.get_bot(bot_cookie)
        opponent = [b for b in self.bots if bot.username != b.username][0]

        winner, reason = self.check_game_over(bot, opponent)
        if winner or reason:
            self.stop()
            return self.inform_game_result(
                winner=winner,
                reason=reason,
                rounds=self.current_round,
            )
        self._game_turn = GameTurn(arena=self.arena, turn_number=self.current_round)

        if self._handle_bot_failure(bot, request) == -1:
            return self.inform_game_result(
                winner=opponent.username,
                reason="Bot {} crashed!!".format(bot.username),
                rounds=self.current_round,
            )

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
        """Evaluate conditions for which the game might end, and process the
        result accordingly. If one of the players won, return the username and
        reason. If it is a draw, return None and the message indicating a tie.
        Otherwise, if it is not the end, of the game, return None, and empty
        message.
        @return :player.username:, :reason<str>:
        """
        opponent_dict = {current_player: opponent, opponent: current_player}
        for pl in (current_player, opponent):
            winner_won, reason = pl.has_won_game(opponent_dict[pl], self.arena)
            if winner_won:
                return pl.username, reason
        if self._rounds_finished():
            winner_username, reason = self._player_with_more_units(current_player, opponent)
            return winner_username, reason
        return None, ""

    def _player_with_more_units(self, player1, player2):
        """Return the player that has more units, and the reason describing
        that.
        @return :winner:, :reason:
        """
        player_with_more_units = max((player1, player2), key=lambda p: len(p.units))
        player_with_less_units = min((player1, player2), key=lambda p: len(p.units))
        if player_with_more_units is not player_with_less_units:
            reason = "Turns limit reached! Player {winner} has more units than Player {loser}".format(
                winner=player_with_more_units.username,
                loser=player_with_less_units.username,
            )
            return player_with_more_units.username, reason
        return None, "Turns limit reached! Both players have the same amount of units!"

    def _rounds_finished(self):
        """Check if the rounds in the game, have finished. @return :bool:"""
        return self.current_round >= self.rounds - 1

    def get_turn_data(self, bot_cookie):
        """Feedback
        :return: the data sent to the bot on each turn
        """
        bot = self.get_bot(bot_cookie)
        return {
            'map': self.arena.get_map_for_player(bot),
            'player_num': bot.p_num,
        }

