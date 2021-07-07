import collections

from terminal_toolkit.ui.TerminalScreen import TerminalScreen
from terminal_toolkit.ui.events.Events import *

if __name__ == '__main__':

    last_mouse_positions = collections.deque(maxlen=10)
    symbols = "*"

    with TerminalScreen("TEST SCREEN", debug=True) as screen:

        for event in screen.events():

            screen.put_str((0, 0), str(event))

            if isinstance(event, MouseEvent):
                x = event.x
                y = event.y
                last_mouse_positions.append((x, y))

            [screen.put_str((x, y), symbols) for (x, y) in last_mouse_positions]

            if isinstance(event, Key):
                symbols = event.key

            screen.write()
