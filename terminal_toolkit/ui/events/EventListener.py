import re
from typing import Tuple

from terminal_toolkit.console import Console
from terminal_toolkit.ui.events.Events import *

regex_mouse_position = r'(?P<x>\d+);(?P<y>\d+)'
regex_mouse_move = r'(?P<escape_code>\x1b\[\<)(?P<mouse_move>35;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_clicked = r'(?P<escape_code>\x1b\[\<)(?P<mouse_clicked>0;)(?P<position>\d+;\d+)(?P<end>M|m)'
regex_mouse_right_clicked = r'(?P<escape_code>\x1b\[\<)(?P<mouse_right_clicked>2;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_dragged = r'(?P<escape_code>\x1b\[\<)(?P<mouse_dragged>32;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_right_dragged = r'(?P<escape_code>\x1b\[\<)(?P<mouse_right_dragged>34;)(?P<position>\d+;\d+)(?P<end>M)'
regex_scroll_up = r'(?P<escape_code>\x1b\[\<)(?P<scroll_up>65;)(?P<position>\d+;\d+)(?P<end>M)'
regex_scroll_down = r'(?P<escape_code>\x1b\[\<)(?P<scroll_down>64;)(?P<position>\d+;\d+)(?P<end>M)'

_curr_mouse_pos = (0, 0)


def get_curr_mouse_pos() -> tuple[int, int]:
    return _curr_mouse_pos


async def async_next_event() -> Event:
    return parse_event(await Console.async_getch())


def next_event() -> Event:
    return parse_event(Console.getch())


def parse_mouse_pos(_in: str) -> Tuple[int, int]:
    """
    this method return the mouse position from a key code
    """

    if match := re.match(pattern=regex_mouse_position, string=_in):
        return int(match.group("x")) - 1, int(match.group("y")) - 1
    else:
        return -1, -1


def parse_event(unparsed_event: str) -> Event:
    """
    this method converts a key code to an Interrupt Event
    """

    global _curr_mouse_pos

    if match := re.match(pattern=regex_mouse_move, string=unparsed_event):
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return MouseMove(x=x, y=y, _unparsed_data=unparsed_event)

    elif match := re.match(pattern=regex_mouse_clicked, string=unparsed_event):
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return Click(x=x, y=y, _unparsed_data=unparsed_event)

    elif match := re.match(pattern=regex_mouse_right_clicked, string=unparsed_event):
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return RightClick(x=x, y=y, _unparsed_data=unparsed_event)

    elif match := re.match(pattern=regex_mouse_dragged, string=unparsed_event):
        from_x, from_y = _curr_mouse_pos
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return MouseDrag(x=x, y=y, from_x=from_x, from_y=from_y, _unparsed_data=unparsed_event)

    elif match := re.match(pattern=regex_mouse_right_dragged, string=unparsed_event):
        from_x, from_y = _curr_mouse_pos
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return MouseRightDrag(x=x, y=y, from_x=from_x, from_y=from_y, _unparsed_data=unparsed_event)

    elif match := re.match(pattern=regex_scroll_up, string=unparsed_event):
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return ScrollUp(x=x, y=y, _unparsed_data=unparsed_event, times=unparsed_event.count("\x1b"))

    elif match := re.match(pattern=regex_scroll_down, string=unparsed_event):
        x, y = _curr_mouse_pos = parse_mouse_pos(_in=match.group("position"))
        return ScrollDown(x=x, y=y, _unparsed_data=unparsed_event, times=unparsed_event.count("\x1b"))

    elif unparsed_event in ModifierKeyCodes.values():
        return ModifierKey(key=ModifierKeyCodes(unparsed_event), _unparsed_data=unparsed_event)

    elif "\x1b" not in unparsed_event and len(unparsed_event) == 1:
        return Key(key=unparsed_event, _unparsed_data=unparsed_event)

    else:
        return UNKNOWN_EVENT(data=unparsed_event, _unparsed_data=unparsed_event)
