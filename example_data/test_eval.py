import sys
from turnboxed.utils import evaluate_in_sandbox

code = """from basebot import BaseBot
from basebot import BaseBot


class Bot(BaseBot):

    def on_turn(self, data_dict):
        return None
"""


def main():
    evaluate_in_sandbox(code)
    sys.exit(0)


if __name__ == "__main__":
    main()
