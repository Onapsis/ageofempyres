from onagame2015.lib import GameBaseObject


class BotPlayer(GameBaseObject):

    def __init__(self, bot_name, script, p_num):
        self.script = script
        self.username = bot_name
        self.p_num = p_num
        self.hq = None
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)

    def remove_unit(self, unit_to_remove):
        self.units = [u for u in self.units if u.id != unit_to_remove.id]

    def has_won_game(self, opponent, arena):
        won = False
        reason = ''
        if arena.enemy_hq_taken(self, opponent):
            reason = "Opponent HQ has been taken"
            won = True
        elif len(opponent.units) == 0:
            reason = "All opponent units have been eliminated"
            won = True
        return won, reason

    def remove_units(self, units_lost):
        for unit in units_lost:
            self.remove_unit(unit)
