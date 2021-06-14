import _io
import asyncio
import os
import shutil
import signal
import sys
import termios
from typing import Any, NewType, Union
from blessings import Terminal
from terminal_toolkit.ui.events.Events import Position

_terminal = Terminal()

HEIGHT = NewType("HEIGHT", int)
WIDTH = NewType("WIDTH", int)


def get_size() -> tuple[WIDTH, HEIGHT]:
    """
    Returns
    -------
    tuple:
        the size of the terminal
    """
    return shutil.get_terminal_size((80, 24))


def set_size(size: tuple[WIDTH, HEIGHT]):
    """
    this function resizes the terminal window

    Parameters
    ----------
    size: tuple
        the new size of the terminal
    """
    width, height = size
    sys.stdout.write(f"\x1b[8;{width};{height}t")
    sys.stdout.flush()


async def wait_resize() -> get_size():
    """
    this function waits until the size of the terminal changes and then return the new size
    Returns
    -------

    """
    resize_event = asyncio.Event()
    asyncio.get_event_loop().add_signal_handler(signal.SIGWINCH, lambda: resize_event.set())
    await resize_event.wait()
    return get_size()


def getch(decode=True,
          stream: _io.TextIOWrapper = sys.stdin) -> Union[str, bytes]:
    """
    getch() reads a single character from the keyboard. But it does not use any buffer, so the entered character is
    immediately returned without waiting for the enter key.

    Parameters
    ----------
    stream : TextIO
        the io stream the getch function is listening to
    decode : bool
        if true the input will be decoded as UTF-8 string

    Returns
    -------
    str or bytes:
        everything written to the stream. see more under mode
    """
    old_settings = new_settings = termios.tcgetattr(stream)
    try:
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        new_settings[6][termios.VMIN] = 1
        new_settings[6][termios.VTIME] = 0
        termios.tcsetattr(stream, termios.TCSADRAIN, new_settings)

        ch = os.read(stream.fileno(), 1)
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        new_settings[6][termios.VMIN] = new_settings[6][termios.VTIME] = 0
        termios.tcsetattr(stream, termios.TCSADRAIN, new_settings)

        while _in := os.read(stream.fileno(), 1):
            ch += _in

        return ch.decode("UTF-8") if decode else ch

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdin.flush()


async def async_getch(decode=True, stream: _io.TextIOWrapper = sys.stdin):
    """
    getch() reads a single character from the keyboard. But it does not use any buffer, so the entered character is
    immediately returned without waiting for the enter key.

    Parameters
    ----------
    stream : TextIO
        the io stream the getch function is listening to
    decode : bool
        if true the input will be decoded as UTF-8 string

    Returns
    -------
    str or bytes:
        everything written to the stream. see more under mode
    """
    old_settings = new_settings = termios.tcgetattr(stream)
    try:
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        new_settings[6][termios.VMIN] = new_settings[6][termios.VTIME] = 0
        termios.tcsetattr(stream, termios.TCSADRAIN, new_settings)

        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.add_reader(stream, future.set_result, None)
        future.add_done_callback(lambda f: loop.remove_reader(stream))
        await future

        ch = os.read(stream.fileno(), 1)
        while _in := os.read(stream.fileno(), 1):
            ch += _in

        return ch.decode("UTF-8") if decode else ch

    finally:
        termios.tcsetattr(stream, termios.TCSADRAIN, old_settings)
        stream.flush()


def put_pixels(pixels: dict[Position, Any]):
    """
    this function allows to place characters on any position in the terminal window

    Parameters
    ----------
    pixels : dict
        this dictionary should contain the positions as keys and the relating character as value
    """
    for x, y in sorted(pixels.keys()):
        sys.stdout.write(_terminal.move(y, x))
        sys.stdout.write(pixels[(x, y)])
    sys.stdout.flush()


def configure(
        fullscreen_mode: bool = False,
        console_echo: bool = True,
        show_cursor: bool = True,
        mouse_movement_reporting: bool = False):
    """
    With this function special functionality of a classic terminal emulator can be activated.
    All changes to the terminal will be undone after the python program ends.

    Parameters
    ----------
    console_echo : bool
        The default is True, if False, everything written to stdin is no longer automatically output to stdout.
        Manual writing to stdout is still possible.
    show_cursor : bool
        The default is True, if False the cursor is no longer displayed.
    fullscreen_mode : bool
        The default is False, if True another mode of the terminal is activated.
        In this mode you can write normally, but everything written disappears when you leave the mode.
        This behavior is known from editors like VIM.
    mouse_movement_reporting :
        The default is False, if True every mouse event (click, scroll, drag, move, ...)
        is written to stdin via special escape-codes.
    """

    # fullscreen mode
    sys.stdout.write(_terminal.enter_fullscreen) if fullscreen_mode else sys.stdout.write(_terminal.exit_fullscreen)

    # console echo
    (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) \
        = termios.tcgetattr(sys.stdin.fileno())
    if console_echo:
        lflag |= termios.ECHO
    else:
        lflag &= ~termios.ECHO
    new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_attr)

    # show cursor
    if show_cursor:
        sys.stdout.write("\033[?25h")
    else:
        sys.stdout.write("\033[?25l")

    # mouse movement reporting
    if mouse_movement_reporting:
        sys.stdout.write("\033[?1002h\033[?1015h\033[?1006h")
        sys.stdout.write("\033[?1003h")
    else:
        sys.stdout.write("\033[?1002l")
        sys.stdout.write("\033[?1003l")

    sys.stdout.flush()
