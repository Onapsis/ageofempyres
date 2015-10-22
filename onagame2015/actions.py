class BaseBotAction(object):
    ACTION_NAME = ''

    def __init__(self, bot):
        self.calling_bog = bot
        self.starting_position = (bot.x, bot.y)
        self.final_position = (bot.x, bot.y)
        self.result = ''

    def action_result(self):
        return {
            'final_position': self.final_position,
            'result': self.result,
        }

    def execute(self):
        pass


class AttackAction(BaseBotAction):
    ACTION_NAME = 'ATTACK'

    def execute(self):
        pass


class MoveAction(BaseBotAction):
    ACTION_NAME = 'MOVE'

    def execute(self):
        pass

