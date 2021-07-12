import asyncio
import time

import terminal_toolkit.ui.TerminalGUI as gui
from terminal_toolkit.ui.events.Events import *
from terminal_toolkit.ui.widgets.Widgtes import TextWidget, PixelWidget

if __name__ == '__main__':

    text_widget = TextWidget("text_widget")

    pixel_widget = PixelWidget("pixel_widget")

    symbol = "#"


    @pixel_widget.event_handler(ScreenClosed)
    def closed_handler(event: ScreenClosed):
        print("GUI CLOSED")
        time.sleep(1)


    @pixel_widget.event_handler(Key)
    def quit_gui(event: Key):
        if event.key == "q":
            gui.quit(0)


    @pixel_widget.event_handler(Key)
    def key_handler(event: Key):
        global symbol
        symbol = event.key


    @pixel_widget.event_handler(MouseDrag)
    def move_handler(event: MouseDrag):
        pixel_widget.add_pixel((event.x, event.y), symbol)


    @pixel_widget.event_handler(ModifierKey)
    def clear_handler(event: ModifierKey):
        if event.key == MODIFIER_KEYS.BACKSPACE:
            pixel_widget.clear()


    gui.mainloop("Hello World", widget=pixel_widget, debug=True)
