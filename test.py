import time
from functools import partial

from terminal import getch
from terminal.styles import rgb, no_color, color_scale
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
    main()
