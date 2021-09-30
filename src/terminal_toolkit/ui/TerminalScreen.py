import collections
import queue
import threading
from typing import AnyStr, Iterable, AsyncIterable, Optional
from time import perf_counter
from statistics import mean

from src.terminal_toolkit.console import Console
from src.terminal_toolkit.console.Console import WIDTH, HEIGHT
from src.terminal_toolkit.ui.events import EventListener
from src.terminal_toolkit.ui.events.Events import Event, Timeout

X = int
Y = int


class TerminalScreen:
    """
    This class provides a programming interface to put characters on specific locations on the terminal screen.
    It also provides an event api that returns Keyboard and Mouse events entered by the user.

    Examples
    --------

    This small programm will print the last pressed key at the current position of the mouse until CONTOL-C is pressed.

    >>> from src.terminal_toolkit import TerminalScreen
    >>> from src.terminal_toolkit import Key
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

    def events(self, timeout: Optional[float] = None) -> Iterable[Event]:
        """
        This generator returns all events the user enters until a KeyboardInterrupt in raised
        (the user terminates the program)

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
            if timeout is None:
                while True:
                    yield EventListener.next_event()
            else:
                events = queue.Queue()

                def _listen():
                    nonlocal events
                    while True:
                        events.put(EventListener.next_event())

                threading.Thread(target=_listen, daemon=True).start()
                while True:
                    try:
                        yield events.get(timeout=timeout)
                    except queue.Empty:
                        yield Timeout()
        except KeyboardInterrupt:
            return

    async def async_events(self) -> AsyncIterable[Event]:
        """
        This generator returns all events the user enters until a KeyboardInterrupt in raised
        (the user terminates the program)

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
            while True:
                yield await EventListener.async_next_event()
        except KeyboardInterrupt:
            return

    def get_mouse_pos(self) -> tuple[X, Y]:
        """
        This method return the current position of the mouse

        Returns
        -------
        tuple:
            the x and y position of the mouse
        """
        return EventListener.get_curr_mouse_pos()

    def get_size(self) -> tuple[WIDTH, HEIGHT]:
        """
        This method return the current size of the terminal screen

        same as: Console.get_size()

        Returns
        -------
        tuple:
            the width and height of the terminal
        """
        return Console.get_size()

    def put_str(self, pos: tuple[X, Y], s: AnyStr):
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
        for c in s:
            self._curr_screen_buf[(x, y)] = c
            x += 1

    def put_pixels(self, pixels: dict[(int, int), AnyStr]):
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
        Console.put_pixels(
            {key: " " for (key, _) in self._last_screen_buf.items()}
        )
        if self.debug:
            Console.set_title(f'{self.title} - draw-time: {mean(self._draw_time):.5f}sek')
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
        Console.put_pixels(
            {key: " " for (key, _) in self._last_screen_buf.items()} | self._curr_screen_buf
        )
        self._draw_time.append(perf_counter() - t1)
        if self.debug:
            Console.set_title(f'{self.title} - draw-time: {mean(self._draw_time):.5f}sec')
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
        Console.set_title(self.title)
        Console.configure(
            fullscreen_mode=True,
            console_echo=False,
            show_cursor=False,
            mouse_movement_reporting=True
        )

    def quit(self):
        """
        This must be called to restore the normal state of the terminal!
        """
        Console.configure(
            fullscreen_mode=False,
            console_echo=True,
            show_cursor=True,
            mouse_movement_reporting=False
        )
        Console.set_title("")

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        print("exit called")
