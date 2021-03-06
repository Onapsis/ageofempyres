import json
from onagame2015.lib import GameStages


class GameStatus(object):
    """Keeps a trace on the status of the game at any given time, so at the end
    it can return the result of the run.
    """

    def __init__(self):
        self._game_data = {stage: {} for stage in GameStages.stages}
        self._reset_actions()

    def _reset_actions(self):
        self._game_data[GameStages.TURNS] = []

    def update_turns(self, new_status):
        """Update self.game_data with the trace of the game.
        :new_status: <dict> with the information for the new action
        """

        self._game_data[GameStages.TURNS].append(new_status)

    def add_game_stage(self, action_key, new_status):
        self._game_data.update({action_key: new_status})

    @property
    def json(self):
        return json.dumps(self._game_data, default=lambda obj: obj.__json__())
