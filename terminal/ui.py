import collections
import queue
import threading
from statistics import mean
from time import perf_counter
from typing import Generator, AsyncGenerator, Literal

from terminal import *
from terminal import WIDTH, HEIGHT
from terminal import events
from terminal.events import Event, Timeout, next_event, ScreenClosed
from terminal.styles import FormatStr

X = int
Y = int


def shift_pixels(pixels: dict[(X, Y), AnyStr], shift: (X, Y)) -> dict[(X, Y), AnyStr]:
    """
    creates a copy of the pixels where every pixel position is shifted by the specified shift

    Parameters
    ----------
    pixels : dict
        to be shifted
    shift : tuple
        the value of how much to shift in x and y direction

    Returns
    -------
    tuple :
        the shifted pixels
    """

    new_pixels = {}
    shift_x, shift_y = shift
    for x, y in pixels:
        new_pixels[(x + shift_x, y + shift_y)] = pixels[(x, y)]
    return new_pixels


def Table(data: dict[str, list[Union[AnyStr, FormatStr]]],
          show_header=True,
          separators: tuple[str, str, str] = (" | ", "-", "+")) -> dict[(X, Y), AnyStr]:
    no_rows = len(data)
    horizontal_sep, vertical_sep, cross_sep = separators
    pixels = {}
    x, y = 0, 0

    row_widths: list[int] = [
        max(len(str(s)) for s in data[key]) for key in data
    ]

    if show_header:
        row = vertical_sep.join(str(FormatStr(header).just(width=row_widths[i], mode="left"))
                                for i, header in enumerate(data.keys()))

        for i, c in enumerate(row):
            pixels[(i, y)] = c

        y += 1

        row = cross_sep.join(str(horizontal_sep) * width
                             for width in row_widths
                             )

        for i, c in enumerate(str(horizontal_sep) * len(row)):
            pixels[(i, y)] = c

        y += 1

    return pixels


class ProgressBar:
    def __init__(self, size: Literal["small", "large"] = "large", show_percentage=True):
        """

        Parameters
        ----------
        size : str
            whether to show a small (1 by 10 characters) or large (1 by 20 characters) bar
        show_percentage : bool
            whether to append the current percentage (adds 7 characters to end)
        """
        self.value = 0
        self.show_percentage = show_percentage
        self.size = size
        if size not in ("small", "large"):
            raise ValueError(f"invalid size: {size}")

    def update(self, percent_done: float):
        """
        update the value of the progressbar

        Parameters
        ----------
        percent_done : float
            the current percent the progress
        """
        self.value = percent_done

    @property
    def _symbols(self) -> dict:
        if self.size == "small":
            return {
                10: "▉",
                9: "▊",
                8: "▊",
                7: "▋",
                6: "▌",
                5: "▌",
                4: "▍",
                3: "▎",
                2: "▏",
                1: "▏",
                0: ""
            }
        elif self.size == "large":
            return {
                10: "▉▉",
                9: "▉▋",
                8: "▉▋",
                7: "▉▍",
                6: "▉▏",
                5: "▉",
                4: "▋",
                3: "▍",
                2: "▏",
                1: "▏",
                0: ""
            }

    def __str__(self):
        curr_value = int(min(100, 100 * self.value))

        result = ""
        i = 0
        while i < curr_value:
            inc = min(10, curr_value - i)
            result += self._symbols[inc]
            i += inc

        width = 20 if self.size == "large" else 10
        if self.show_percentage:
            width += 7

        if self.show_percentage:
            result += f' {curr_value:.1f}%'

        return result


class StatusWheel:
    """
    this class produces a small progress wheel.
    usage: make an instance of this object.
    every time __str__ is called on this object the next symbol is returned
    """

    def __init__(self, size: Literal["small", "large"] = "large"):
        """

        Parameters
        ----------
        size :
            whether to display a small (1 by 3 characters) or small (1 by 1 character) status wheel
        """
        self.num = 0
        self.size = size

        self.__symbols__ = {
            0: "▁",
            1: "▃",
            2: "▄",
            3: "▅",
            4: "▆",
            5: "▆",
            6: "▇",
            7: "█",
            8: "▇",
            9: "▆",
            10: "▆",
            11: "▅",
            12: "▄",
            13: "▃",
            14: "▁",
        }

        if size not in ("large", "small"):
            raise ValueError(f"invalid size: {size}")

    @property
    def _symbols(self) -> dict:
        if self.size == "large":
            return {
                0: "[|]",
                1: "[/]",
                2: "[-]",
                3: "[\\]"
            }
        elif self.size == "small":
            return {
                8: "⣾",
                7: "⣽",
                6: "⣻",
                5: "⢿",
                4: "⡿",
                3: "⣟",
                2: "⣟",
                1: "⣯",
                0: "⣷"
            }

    def __str__(self) -> str:
        self.num += 1
        return self._symbols[self.num % len(self._symbols)]


class TerminalScreen:
    """
    This class provides a programming interface to put characters on specific locations on the terminal screen.
    It also provides an event api that returns Keyboard and Mouse events entered by the user.

    Examples
    --------

    This small programm will print the last pressed key at the current position of the mouse until CONTOL-C is pressed.

    >>> from terminal.ui import TerminalScreen
    >>> from terminal.events import Key
    >>> # initialize terminal screen
    >>> with TerminalScreen("My Title") as screen:
    >>> # main event loop
    >>>     for event in screen.events():
    >>>         # if the user presses a key, display it at the current mouse position
    >>>         if isinstance(event, Key):
    >>>             screen.put_str(screen.get_mouse_pos(), event.key)
    >>>         # display the current event at the top left corner of the screen
    >>>         screen.put_str((0,0), str(event))
    >>>         # write all characters to the screen, only after this changes will take effect
    >>>         screen.write()


    The class also support asyncio. All that has to be changed is to use the asnyc_events method:

    >>> async for event in screen.async_events():
    >>> ...
    """

    def __init__(self, title: str, debug: bool = False):
        """
        Creates a new TerminalScreen only one TerminalScreen can be created at once
        Parameters
        ----------
        title
        debug
        """
        self.title = title
        self.debug = debug
        self._draw_time = collections.deque(maxlen=50)
        self._curr_screen_buf = {}
        self._last_screen_buf = {}
        self._size = self.get_size()

    def events(self, timeout: Optional[float] = None) -> Generator[Event, None, None]:
        """
        This generator returns all events the user enters until a KeyboardInterrupt in raised
        (the user terminates the program)
        If the user terminates the programm the ScreenClosed Event will be returned

        Usage
        -----
        >>> # gui main loop
        >>> for event in screen.events():
        >>>     # handle events here

        Parameters
        ----------
        timeout : float
            If the timeout value is not None, a sepperate thread will be started to listen for events.
            The generator then only blocks for the value specified as timeout. If a timeout occurs, the "Timeout" event
            is returned.

        Yields
        -------
        Events
            an event object that can be quried to get the user input
        """
        try:
            configure(
                mouse_movement_reporting=True,
                console_echo=None,
                fullscreen_mode=None,
                show_cursor=None
            )
            if timeout is None:
                while True:
                    yield next_event()
            else:
                events = queue.Queue()

                def _listen():
                    nonlocal events
                    while True:
                        events.put(next_event())

                threading.Thread(target=_listen, daemon=True).start()
                while True:
                    try:
                        yield events.get(timeout=timeout)
                    except queue.Empty:
                        yield Timeout()
        except KeyboardInterrupt:
            yield ScreenClosed()
        finally:
            configure(
                mouse_movement_reporting=False,
                console_echo=None,
                fullscreen_mode=None,
                show_cursor=None
            )

    async def async_events(self) -> AsyncGenerator[Event, None]:
        """
        This generator returns all events the user enters until a KeyboardInterrupt in raised
        (the user terminates the program)
        If the user terminates the programm the ScreenClosed Event will be returned

        Usage
        -----
        >>> # gui main loop
        >>> async for event in screen.async_events():
        >>>     # handle events here

        Yields
        -------
        Events
            an event object that can be quried to get the user input
        """
        try:
            configure(
                mouse_movement_reporting=True,
                console_echo=None,
                fullscreen_mode=None,
                show_cursor=None
            )
            while True:
                yield await events.async_next_event()
        except KeyboardInterrupt:
            yield ScreenClosed()
        finally:
            configure(
                mouse_movement_reporting=False,
                console_echo=None,
                fullscreen_mode=None,
                show_cursor=None
            )

    def get_mouse_pos(self) -> tuple[X, Y]:
        """
        This method return the current position of the mouse

        Returns
        -------
        tuple:
            the x and y position of the mouse
        """
        return events.get_curr_mouse_pos()

    def get_size(self) -> tuple[WIDTH, HEIGHT]:
        """
        This method return the current size of the terminal screen

        same as: Console.get_size()

        Returns
        -------
        tuple:
            the width and height of the terminal
        """
        return get_size()

    def put_str(self, pos: tuple[X, Y], s: Union[AnyStr, FormatStr]):
        """
        This method adds the string to the current screen buffer at the specified location. To make this string
        (and everything else in the screen buffer) show up, the write() method must be invoked

        Usage
        -----
        >>> # display welcome message on the top left of the screen
        >>> screen.put_str((0,0), "Hello World")
        >>> screen.write()

        Parameters
        ----------
        pos : tuple
            the x and y position of the first char of the string
        s : AnyStr
            the string
        """
        x, y = pos
        s = s if isinstance(s, FormatStr) else FormatStr(s)
        for c in s:
            self._curr_screen_buf[(x, y)] = c
            x += 1

    def put_pixels(self, pixels: dict[(X, Y), AnyStr]):
        """
        This adds a pixel dict directly to the current screen buffer. The keys must be tuples of two integers,
        representing the x and y position and the values must AnyStr.

        Parameters
        ----------
        pixels : dict
            will be added to the current screen buffer
        """
        self._curr_screen_buf |= pixels

    def empty_screen_buffer(self):
        """
        This method clears the current screen buffer.
        This is automatically done when using the write method, which writes the buffer to the screen before clearing it.
        """
        self._curr_screen_buf = {}

    def clear_screen(self):
        """
        This method removes all pixels currently displayed on the screen. This does not affect the current screen buffer.
        """
        t1 = perf_counter()
        put_pixels(
            {key: " " for (key, _) in self._last_screen_buf.items()}
        )
        if self.debug:
            set_title(f'{self.title} - draw-time: {mean(self._draw_time):.5f}sek')
        self._last_screen_buf = {}

    def write(self):
        """
        This method writes the current screen buffer to the screen. All characters currently displayed will be removed
        if they weren't added to the screen buffer again
        """
        t1 = perf_counter()
        if self._size != self.get_size():
            x, y = self._size = self.get_size()
            for i in range(x):
                for j in range(y):
                    self._last_screen_buf[(i, j)] = " "
        put_pixels(
            {key: " " for (key, _) in self._last_screen_buf.items()} | self._curr_screen_buf
        )
        self._draw_time.append(perf_counter() - t1)
        if self.debug:
            set_title(f'{self.title} - draw-time: {mean(self._draw_time):.5f}sec')
        self._last_screen_buf = self._curr_screen_buf
        self._curr_screen_buf = {}

    def get_avg_write_time(self) -> float:
        """
        Returns
        -------
        float :
            returns the average time it takes to draw a frame on the screen. This time is th mean of the last 50 times the
            write method was called

        """
        return mean(self._draw_time)

    def show(self):
        """
        Dragons be here!

        Starts the TerminalScreen. Before termination screen.quit() MUST be called! To enshure this,
        it is recommended to use the screen with the contextmanager:

        >>> with TerminalScreen("Title") as screen:
        >>>         ... # main event loop
        >>> # the contextmanager calls quit on exit automatically

        Warnings
        --------
        If screen.quit() is not a called before the program exists, the terminal will be unusable!
        """
        set_title(self.title)
        configure(
            console_echo=False,
            fullscreen_mode=True,
            show_cursor=False,
        )

    def quit(self):
        """
        This must be called to restore the normal state of the terminal!
        """
        configure(
            console_echo=True,
            fullscreen_mode=False,
            show_cursor=True,
        )
        set_title("")

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
