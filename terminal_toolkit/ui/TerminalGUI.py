from terminal_toolkit.ui.TerminalScreen import TerminalScreen
from terminal_toolkit.ui.widgets.BaseClasses import BaseWidget


class TerminalGUI:
    """
    This is a high level programming interface to build a callback based gui in the terminal.
    """
    def __init__(self, title: str, debug: bool = False):
        self.title = title
        self.debug = debug

    def add_widget(self, widget: BaseWidget):
        pass

    def remove_widget(self, widget: BaseWidget):
        pass

    def main(self):
        """
        The main program loop
        """
        with TerminalScreen(self.title, self.debug) as screen:
            pass
