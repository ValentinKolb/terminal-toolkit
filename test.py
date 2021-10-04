import re
from re import Pattern
import time
from functools import partial

from terminal import getch
from terminal.string import tokenize
from terminal.color import no_color, color, rgb, color_scale
from terminal.ui import TerminalScreen, ProgressBar

my_scale = partial(color_scale, domain=(0, 1), color_range=(rgb(255, 0, 0), rgb(0, 255, 0)))


def main():
    data = {
        "Row 1": list(range(10)),
        "Row 2": list(range(10, 100, 10))
    }

    # table = Table(data)

    bar = ProgressBar()

    i = 0

    with TerminalScreen("Test") as screen:
        screen: TerminalScreen
        for i in (i / 100 for i in range(0, 101)):
            bar.update(i)
            screen.put_str((0, 0), f'{my_scale(i):c}{bar}{no_color()}')
            i += 0.01
            screen.write()
            time.sleep(.01)

        getch()


if __name__ == '__main__':

    s = f'Test0 - {color("red"):c}' + f"{color('yellow'):bg}TESTTESTTEST{color('blue'):bg}" * 200 + \
                  f'{color("green"):c}' + f"TESTT{color('red'):bg}ESTTEST{color('black'):bg}" * 200

    t = time.perf_counter()
    for c in tokenize(s):
        print(c, end="", flush=False)
    print()
    print(time.perf_counter() - t)
