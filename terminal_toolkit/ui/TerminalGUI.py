from terminal_toolkit.ui.TerminalScreen import TerminalScreen
from terminal_toolkit.ui.events.Events import ScreenClosed
from terminal_toolkit.ui.widgets.BaseClasses import BaseWidget


def serve(title: str, widget: BaseWidget, debug: bool = False):
    with TerminalScreen(title, debug) as screen:
        screen.put_pixels(widget.to_pixels(screen.get_size(), screen.get_size()))
        screen.write()
        for event in screen.events():
            widget.handle_event(event)
            screen.put_pixels(widget.to_pixels(screen.get_size(), screen.get_size()))
            if debug:
                _, y = screen.get_size()
                screen.put_str((0, y-1), f'size={screen.get_size()} {event=}')

            screen.write()
        widget.handle_event(ScreenClosed(_unparsed_data=""))
