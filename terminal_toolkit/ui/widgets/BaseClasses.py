from __future__ import annotations

import abc
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import AnyStr

from terminal_toolkit.ui.events.Events import Event


@dataclass
class BaseCallback(metaclass=abc.ABCMeta):
    """
    Base class to all callbacks invoked on widgets
    """
    event: Event

    @abstractmethod
    def handle(self, event: Event, widget: BaseWidget):
        ...


@dataclass
class BaseWidget(metaclass=abc.ABCMeta):
    """
    Base class to all widgets
    """
    name: str
    style: dict
    callbacks: list[BaseCallback] = field(default_factory=list())

    @abstractmethod
    def to_pixels(self) -> dict[tuple[int, int], AnyStr]:
        ...
