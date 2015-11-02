from turnboxed.gamecontroller import BaseGameController
from onagame2015.actions import BaseBotAction, MoveAction
from onagame2015.status import GameStatus
from onagame2015.arena import ArenaGrid
from onagame2015.turn import GameTurn
from onagame2015.lib import (
    GameStages,
    GameBaseObject,
    STARTS_WITH_N_UNITS,
    GameOverException
)


class Onagame2015GameController(BaseGameController):

    def __init__(self, bots):
        BaseGameController.__init__(self)
        self.arena = ArenaGrid()
        self.bots = bots
        self.rounds = 4
        self._actions = {cls.ACTION_NAME: cls for cls in BaseBotAction.__subclasses__()}
        self.game_status = GameStatus()
        self.deploy_players()

    def deploy_players(self):
        initial_status = {
            "map_source": "map1_100x100.json",
            "fog_range": 1,
            'players': [],
        }
        for bot, color in zip(self.bots, ("0x000077", "0xFF0000")):
            initial_coordinate = self.arena.random_initial_player_location(bot)
            self.arena.add_units_to_player(bot)
            player_data = {
                'name': bot,
                'color': color,
                'position': {'x': initial_coordinate.latitude, 'y': initial_coordinate.longitude},
                'units': STARTS_WITH_N_UNITS,
            }
            initial_status['players'].append(player_data)
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
        for action_key, new_status in self._game_turn.end_turn_status():
            self.game_status.update_turns(action_key, new_status)

    def _handle_bot_failure(self, bot, request):
        """Manage the case if one of the bots failed,
        in that case, stop the execution, and log accordingly.
        """
        if "EXCEPTION" in request:
            # bot failed in turn
            self.log_msg("Bot %s crashed: %s %s" % (bot.username, request['EXCEPTION'], request['TRACEBACK']))
            self.stop()
            return -1

    def inform_result(self, winner=None, reason=None):
        final_status = {
            'action': 'GAMEOVER',
            'reason': reason,
            'result': winner and 'WIN' or 'DRAW',
            'player': winner or '',
        }
        self.game_status.add_game_stage(GameStages.FINAL, final_status)

    def evaluate_turn(self, request, bot_cookie):
        """
        # Game logic here.
        @return: <int>
        """
        bot = self.get_bot(bot_cookie)
        self._game_turn = GameTurn(arena=self.arena)
        if self._handle_bot_failure(bot, request) == -1:
            opponent = [b for b in self.bots if bot.username != b.username][0]
            self.inform_result(winner=opponent,
                               reason="Bot {} crashed!!".format(bot.username))
            return -1

        self.log_msg("GOT Action: %s" % request['MSG']['ACTIONS'])
        self._validate_actions(request['MSG']['ACTIONS'])

        for action in request['MSG']['ACTIONS']:
            bot_action_type = self._actions.get(action['action_type'], BaseBotAction)
            bot = self.get_bot(bot_cookie)
            result = bot_action_type(bot).execute(self.arena, action)
            self._game_turn.evaluate_bot_action(result)
        self.check_game_over()
        self._update_game_status()
        return 0

    def check_game_over(self):
        pass

    def get_turn_data(self, bot_cookie):
        """Feedback
        :return: the data sent to the bot on each turn
        """
        bot = self.get_bot(bot_cookie)
        return {
            'map': self.arena.get_map_for_player(bot),
            'player_num': bot.p_num,
        }


class BotPlayer(GameBaseObject):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq = None
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)
