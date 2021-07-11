from __future__ import annotations

import abc
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import AnyStr, Callable, DefaultDict, TypeVar, Any, Type

from terminal_toolkit.style.BaseWidgetStyle import WidgetStyle
from terminal_toolkit.ui.events import Events

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class BaseWidget(metaclass=abc.ABCMeta):
    """
    Base class to all widgets
    """
    name: str
    style: WidgetStyle = field(default_factory=WidgetStyle)
    callbacks: DefaultDict[Type[Events.Event], list] = field(default_factory=lambda: defaultdict(list), init=False)

    @abstractmethod
    def to_pixels(self, abs_size: tuple[int, int], rel_size: tuple[int, int]) -> dict[tuple[int, int], AnyStr]:
        ...

    @abstractmethod
    def handle_event(self, event: Events.Event):
        ...

    @abstractmethod
    async def async_handle_event(self, event: Events.Event):
        ...

    def event_handler(self, event_type: Type[Events.Event]) -> Callable[[F], F]:
        def handle(f):
            self.callbacks[event_type].append(f)
            return f

        return handle
