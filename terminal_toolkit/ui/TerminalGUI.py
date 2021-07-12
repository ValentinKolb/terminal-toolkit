import sys

from terminal_toolkit.mixed import ProgressIndicator
from terminal_toolkit.ui.TerminalScreen import TerminalScreen
from terminal_toolkit.ui.events.Events import ScreenClosed, Timeout
from terminal_toolkit.ui.widgets.BaseClasses import BaseWidget


def exit(status: int = 0):
    """
    quits the gui and exits the program

    Parameters
    ----------
    status : int
        the exit code of the program
    """
    sys.exit(status)


def mainloop(title: str, widget: BaseWidget, framerate: float = .1, debug: bool = False):
    last_event = None
    wheel = ProgressIndicator.Wheel()
    with TerminalScreen(title) as screen:
        screen.put_pixels(widget.to_pixels(screen.get_size(), screen.get_size()))
        screen.write()
        for event in screen.events(timeout=framerate):
            widget.handle_event(event)
            screen.put_pixels(widget.to_pixels(screen.get_size(), screen.get_size()))
            if debug:
                last_event = event if not isinstance(event, Timeout) else last_event
                x, y = screen.get_size()
                screen.put_str((0, y - 1),
                               f'{str(wheel)} size={(x, y)} avg_draw_time={(screen.get_avg_write_time() * 1000):.3f}ms '
                               f'{last_event=}'
                               f'{" [Timeout]" if isinstance(event, Timeout) else ""}')

            screen.write()
        widget.handle_event(ScreenClosed())
