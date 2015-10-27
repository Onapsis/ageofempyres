class BaseBotAction(object):
    ACTION_NAME = ''

    def __init__(self, bot):
        self.calling_bog = bot
        self.result = ''

    def action_result(self):
        return {
            'result': self.result,
        }

    def execute(self, arena, action):
        pass


class AttackAction(BaseBotAction):
    ACTION_NAME = 'ATTACK'

    def execute(self, arena, action):
        # TODO: When a soldier attack, the enemy must be front of him and it must be from other team
        pass


class MoveAction(BaseBotAction):
    ACTION_NAME = 'MOVE'

    def execute(self, arena, action):
        unit = arena.get_unit(action['unit_id'])
        if unit:
            unit.move(action['direction'])
