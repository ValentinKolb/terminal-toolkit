from abc import ABC
from dataclasses import dataclass, field
from typing import Union

from collections import namedtuple
from enum import unique, Enum

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
    _unparsed_data: str = field(repr=False)


@dataclass(frozen=True)
class UNKNOWN_EVENT(Event):
    data: str


@dataclass(frozen=True)
class MouseEvent(Event):
    x: int
    y: int


@dataclass(frozen=True)
class KeyboardEvent(Event):
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


@dataclass(frozen=True)
class ScreenClosed(Event):
    ...
