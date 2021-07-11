import collections

import terminal_toolkit.ui.TerminalGUI as gui
from terminal_toolkit.console import Console
from terminal_toolkit.ui.events.Events import *
from terminal_toolkit.ui.widgets.Widgtes import TextWidget, PixelWidget

if __name__ == '__main__':
    text_widget = TextWidget("text_widget")

    pixel_widget = PixelWidget("pixel_widget")

    symbol = "#"


    @pixel_widget.event_handler(Key)
    def key_handler(event: Key, widget: PixelWidget):
        global symbol
        symbol = event.key


    @pixel_widget.event_handler(MouseDrag)
    def move_handler(event: MouseDrag, widget: PixelWidget):
        widget.add_pixel((event.x, event.y), symbol)


    @pixel_widget.event_handler(ModifierKey)
    def clear_handler(event: ModifierKey, widget: PixelWidget):
        if event.key == MODIFIER_KEYS.BACKSPACE:
            widget.clear()


    gui.serve("Hello World", widget=pixel_widget, debug=True)
