from abc import ABC
from collections import namedtuple
from dataclasses import dataclass, field
from enum import unique, Enum
from typing import Tuple

from terminal import *

regex_mouse_position = r'(?P<x>\d+);(?P<y>\d+)'
regex_mouse_move = r'(?P<escape_code>\x1b\[\<)(?P<mouse_move>35;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_clicked = r'(?P<escape_code>\x1b\[\<)(?P<mouse_clicked>0;)(?P<position>\d+;\d+)(?P<end>M|m)'
regex_mouse_right_clicked = r'(?P<escape_code>\x1b\[\<)(?P<mouse_right_clicked>2;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_dragged = r'(?P<escape_code>\x1b\[\<)(?P<mouse_dragged>32;)(?P<position>\d+;\d+)(?P<end>M)'
regex_mouse_right_dragged = r'(?P<escape_code>\x1b\[\<)(?P<mouse_right_dragged>34;)(?P<position>\d+;\d+)(?P<end>M)'
regex_scroll_up = r'(?P<escape_code>\x1b\[\<)(?P<scroll_up>65;)(?P<position>\d+;\d+)(?P<end>M)'
regex_scroll_down = r'(?P<escape_code>\x1b\[\<)(?P<scroll_down>64;)(?P<position>\d+;\d+)(?P<end>M)'

_curr_mouse_pos = (0, 0)

Position = namedtuple("Position", "x y")


@unique
class MODIFIER_KEYS(Enum):
    ENTER = '\n'
    ESC = '\x1b'
    TAB = '\t'
    REVERSE_TAB = '\x1b[Z'
    BACKSPACE = '\x7f'
    DELETE = '\x1b[3~'
    UP_ARROW = '\x1b[A'
    DOWN_ARROW = '\x1b[B'
    RIGHT_ARROW = '\x1b[C'
    LEFT_ARROW = '\x1b[D'
    OPTION_LEFT = '\x1bb'
    OPTION_RIGHT = '\x1bf'
    CONTROL_X = '\x18'
    CONTROL_V = '\x16'
    CONTROL_B = '\x02'
    CONTROL_N = '\x0e'
    CONTROL_A = '\x01'
    CONTROL_D = '\x04'
    CONTROL_F = '\x06'
    CONTROL_G = '\x07'
    CONTROL_H = '\x08'
    CONTROL_K = '\x0b'
    CONTROL_L = '\x0c'
    CONTROL_W = '\x17'
    CONTROL_E = '\x05'
    CONTROL_R = '\x12'
    CONTROL_T = '\x14'
    CONTROL_U = '\x15'
    CONTROL_P = '\x10'
    F1 = '\x1bOP'
    F2 = '\x1bOQ'
    F3 = '\x1bOR'
    F4 = '\x1bOS'
    F5 = '\x1b[15~'
    F6 = '\x1b[17~'
    F7 = '\x1b[18~'
    F8 = '\x1b[19~'
    F9 = '\x1b[20~'
    F10 = '\x1b[21~'

    @classmethod
    def values(cls):
        return [enum.value for enum in cls]

    @classmethod
    def names(cls):
        return [enum.name for enum in cls]


@dataclass(frozen=True)
class Event(ABC):
    ...


@dataclass(frozen=True)
class ScreenClosed(Event):
    ...


@dataclass(frozen=True)
class Timeout(Event):
    ...


@dataclass(frozen=True)
class InputEvent(Event):
    _unparsed_data: str = field(repr=False)


@dataclass(frozen=True)
class UNKNOWN_EVENT(InputEvent):
    data: str


@dataclass(frozen=True)
class MouseEvent(InputEvent):
    x: int
    y: int


@dataclass(frozen=True)
class KeyboardEvent(InputEvent):
    key: Union[str, MODIFIER_KEYS]


@dataclass(frozen=True)
class Key(KeyboardEvent):
    ...


@dataclass(frozen=True)
class ModifierKey(KeyboardEvent):
    ...


@dataclass(frozen=True)
class Click(MouseEvent):
    ...


@dataclass(frozen=True)
class RightClick(MouseEvent):
    ...


@dataclass(frozen=True)
class MouseMove(MouseEvent):
    ...


@dataclass(frozen=True)
class MouseDrag(MouseEvent):
    from_x: int
    from_y: int


@dataclass(frozen=True)
class MouseRightDrag(MouseDrag):
    ...


@dataclass(frozen=True)
class MouseOn(MouseEvent):
    ...


@dataclass(frozen=True)
class MouseOff(MouseEvent):
    ...


@dataclass(frozen=True)
class ScrollUp(MouseEvent):
    times: int


@dataclass(frozen=True)
class ScrollDown(MouseEvent):
    times: int


def get_curr_mouse_pos() -> tuple[int, int]:
    return _curr_mouse_pos


async def async_next_event() -> Event:
    return parse_event(await async_getch())


def next_event() -> Event:
    return parse_event(getch())


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

    elif unparsed_event in MODIFIER_KEYS.values():
        return ModifierKey(key=MODIFIER_KEYS(unparsed_event), _unparsed_data=unparsed_event)

    elif "\x1b" not in unparsed_event and len(unparsed_event) == 1:
        return Key(key=unparsed_event, _unparsed_data=unparsed_event)

    else:
        return UNKNOWN_EVENT(data=unparsed_event, _unparsed_data=unparsed_event)
