import _io
import asyncio
import os
import re
import shutil
import signal
import sys
import termios
from typing import Union, AnyStr, Optional

HEIGHT = int
WIDTH = int
ROW = int
COLUMN = int


def get_size() -> tuple[WIDTH, HEIGHT]:
    """
    Returns
    -------
    tuple:
        the size of the terminal
    """
    w, h = shutil.get_terminal_size((80, 24))
    return w, h


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


def set_title(title: str, flush=True):
    """
    sets the title of the terminal window

    Parameters
    ----------
    title : str
        will become the new title of the window
    flush : True
        whether to flush stdout. the title will not be set until stdout has been flushed.

    """
    sys.stdout.write(f'\033]2;{title}\007')
    sys.stdout.flush() if flush else None


async def async_wait_resize() -> get_size():
    """
    this function waits until the size of the terminal changes and then return the new size

    Returns
    -------
    tuple :
        the new size of the terminal
    """
    resize_event = asyncio.Event()
    asyncio.get_event_loop().add_signal_handler(signal.SIGWINCH, lambda: resize_event.set())
    await resize_event.wait()
    return get_size()


def getch(stream: _io.TextIOWrapper = sys.stdin, blocking: bool = True, decode=True) -> Union[str, bytes]:
    """
    getch() reads a single character from the keyboard. But it does not use any buffer, so the entered character is
    immediately returned without waiting for the enter key. the char will not be printed to the terminal!

    Parameters
    ----------
    stream : TextIO
        the io stream the getch method is listening to
    blocking : bool
        if blocking, getch will block until a byte is written to the stream. if not blocking getch will eminently
        return. the return value will be either the bytes previously written to the stream or None
    decode : bool
        if true the input will be decoded as UTF-8 string

    Returns
    -------
    str:
        everything written to the stream. see more under mode
    """
    old_settings = termios.tcgetattr(stream)
    new_settings = old_settings.copy()
    try:
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        new_settings[6][termios.VTIME] = 0
        if blocking:
            new_settings[6][termios.VMIN] = 1
        else:
            new_settings[6][termios.VMIN] = 0
        termios.tcsetattr(stream, termios.TCSADRAIN, new_settings)
        ch = os.read(stream.fileno(), 1)
        if blocking:
            new_settings[6][termios.VMIN] = 0
            termios.tcsetattr(stream, termios.TCSADRAIN, new_settings)
        while _in := os.read(stream.fileno(), 1):
            ch += _in
        return ch.decode("UTF-8") if decode else ch
    finally:
        termios.tcsetattr(stream, termios.TCSADRAIN, old_settings)
        stream.flush()


async def async_getch(decode=True, stream: _io.TextIOWrapper = sys.stdin) -> Union[str, bytes]:
    """
    getch() reads a single character from the keyboard. But it does not use any buffer, so the entered character is
    immediately returned without waiting for the enter key. the char will not be printed to the terminal!

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
    old_settings = termios.tcgetattr(stream)
    new_settings = old_settings.copy()
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


def move_cursor(pos: tuple[ROW, COLUMN], flush=True):
    """
    this function moves the cursor to the specified location on the terminal screen

    Parameters
    ----------
    flush : bool
        whether to flush stdout. the cursor does not move until stdout has been flushed.
    pos : tuple
        the x and y position where to move the cursor

    """
    x, y = pos
    sys.stdout.write(f"\033[{y + 1};{x + 1}H")
    sys.stdout.flush() if flush else None


def move_cursor_right(steps: int = 1, flush: bool = True):
    """
    this function moves the cursor to the right on the terminal screen without printing a space

    Parameters
    ----------
    flush : bool
        whether to flush stdout. the cursor does not move until stdout has been flushed.
    steps : int
        the number of columns to move
    """
    sys.stdout.write(f"\033[{steps}C")
    sys.stdout.flush() if flush else None


def move_cursor_left(steps: int = 1, flush: bool = True):
    """
    this function moves the cursor to the left on the terminal screen without deleting any characters

    Parameters
    ----------
    flush : bool
        whether to flush stdout. the cursor does not move until stdout has been flushed.
    steps : int
        the number of columns to move
    """
    sys.stdout.write(f"\033[{steps}D")
    sys.stdout.flush() if flush else None


def move_cursor_up(steps: int = 1, flush: bool = True):
    """
        this function moves the cursor up on the terminal screen without deleting any characters

        Parameters
        ----------
        flush : bool
            whether to flush stdout. the cursor does not move until stdout has been flushed.
        steps : int
            the number of columns to move
        """
    sys.stdout.write(f"\033[{steps}A")
    sys.stdout.flush() if flush else None


def move_cursor_down(steps: int = 1, flush: bool = True):
    """
        this function moves the cursor down on the terminal screen without

        Parameters
        ----------
        flush : bool
            whether to flush stdout. the cursor does not move until stdout has been flushed.
        steps : int
            the number of columns to move
        """
    sys.stdout.write(f"\033[{steps}B")
    sys.stdout.flush() if flush else None


def get_cursor_pos() -> tuple[ROW, COLUMN]:
    """
    this function return the current position of the cursor on the terminal. to get this info it uses ansi escape
    code and therefore writes to stdout, flushes it and reads from stdin! be aware that this can cause undefined
    behavior if you application also uses these streams at the same time or written something to stdout without
    flushing it

    Returns
    -------
    tuple :
        the row and column where the cursor is located
    """
    sys.stdout.write("\033[6n")
    sys.stdout.flush()
    while not (_in := getch()).endswith("R"):
        pass
    match = re.match(pattern=r".*\[(?P<row>\d+);(?P<column>\d+)R", string=_in)
    return ROW(int(match.group("row"))), COLUMN(int(match.group("column")))


def save_cursor_pos():
    """
    this save the cursor position. this position can be restored with the restore_cursor_pos function

    See Also
    --------
    restore_cursor_pos : restores the saved position
    """
    sys.stdout.write("\033[s")
    sys.stdout.flush()


def restore_cursor_pos():
    """
    this functions restores the cursor pos if it was saved before with the save_cursor_pos function

    See Also
    --------
    save_cursor_pos : saves the position to be restored with this function
    """
    sys.stdout.write("\033[u")
    sys.stdout.flush()


def erase_end_of_line(flush=True):
    """
    this function deletes the end of the line from the position of the cursor

    Parameters
    ----------
    flush : bool
        whether to flush stdout. the cursor does not move until stdout has been flushed.
    """
    sys.stdout.write(f"\033[K")
    sys.stdout.flush() if flush else None


def put_pixels(pixels: dict[tuple[int, int], AnyStr], flush=True):
    """
    this function allows to place characters on any position in the terminal window

    Parameters
    ----------
    pixels : dict
        this dictionary should contain the positions as keys and the relating character as value
    flush : bool
         whether to flush stdout. the characters will not be shown until stdout has been flushed.
    """
    width, height = get_size()
    for x, y in sorted(pixels.keys(), key=lambda t: t[1]):
        if 0 <= x < width and 0 <= y < height:
            move_cursor((x, y), flush=False)
            sys.stdout.write(pixels[(x, y)])
    sys.stdout.flush() if flush else None


def configure(
        fullscreen_mode: Optional[bool] = False,
        console_echo: Optional[bool] = True,
        show_cursor: Optional[bool] = True,
        mouse_movement_reporting: Optional[bool] = False):
    """
    With this function special functionality of a classic terminal emulator can be activated.
    All changes to the terminal will be undone after the python program ends.

    To not change a attribute, set it to None.

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
    (sys.stdout.write('\x1b[?1049h') if fullscreen_mode else sys.stdout.write('\x1b[?1049l')) \
        if fullscreen_mode is not None else None

    # console echo
    (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) \
        = termios.tcgetattr(sys.stdin.fileno())
    if console_echo:
        lflag |= termios.ECHO
    else:
        lflag &= ~termios.ECHO
    new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_attr) if console_echo is not None else None

    # show cursor
    if show_cursor is None:
        pass
    elif show_cursor:
        sys.stdout.write("\033[?25h")
    else:
        sys.stdout.write("\033[?25l")

    # mouse movement reporting
    if mouse_movement_reporting is None:
        pass
    elif mouse_movement_reporting:
        sys.stdout.write("\033[?1002h\033[?1015h\033[?1006h")
        sys.stdout.write("\033[?1003h")
    else:
        sys.stdout.write("\033[?1002l")
        sys.stdout.write("\033[?1003l")

    sys.stdout.flush()
