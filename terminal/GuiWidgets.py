from __future__ import annotations

import abc
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import AnyStr, Callable, DefaultDict, Any, Type, final
from terminal.Events import Event
from Styles import WidgetStyle


@dataclass
class BaseWidget(metaclass=abc.ABCMeta):
    """
    Base class to all widgets
    """
    name: str
    style: WidgetStyle = field(default_factory=WidgetStyle)
    callbacks: DefaultDict[Type[Event], list[Callable[[Event], Any]]] = \
        field(default_factory=lambda: defaultdict(list), init=False)

    @abstractmethod
    def to_pixels(self, abs_size: tuple[int, int], rel_size: tuple[int, int]) -> dict[tuple[int, int], AnyStr]:
        ...

    @abstractmethod
    def handle_event(self, event: Event):
        ...

    def event_handler(self, event_type: Type[Event]) \
            -> Callable[[Callable[[Event], Any]], Callable[[Event], Any]]:
        def handle(f):
            self.callbacks[event_type].append(f)
            return f

        return handle


@dataclass
class Widget(BaseWidget, abc.ABC):

    @final
    def handle_event(self, event: Event):
        for handler in self.callbacks[type(event)]:
            handler(event)


@dataclass
class PixelWidget(Widget):
    pixels: dict[(int, int), AnyStr] = field(default_factory=dict)

    def clear(self):
        self.pixels = {}

    def add_pixel(self, pos: tuple[int, int], pixel: AnyStr):
        self.pixels[pos] = pixel

    def to_pixels(self, abs_size: tuple[int, int], rel_size: tuple[int, int]) -> dict[tuple[int, int], AnyStr]:
        pixels = {}

        width, height = self.style.size.get_size(abs_size, rel_size)

        for x in range(width):
            for y in range(height):
                if (x, y) in self.pixels:
                    pixels[(x, y)] = self.pixels[(x, y)]

        return pixels


@dataclass
class TextWidget(Widget):
    text: str = ""

    def set_text(self, text: AnyStr):
        if not isinstance(text, str):
            raise ValueError("text must be type of AnyStr")

        self.text = text

    def to_pixels(self, abs_size: tuple[int, int], rel_size: tuple[int, int]) -> dict[tuple[int, int], AnyStr]:
        pixels = {}

        width, height = self.style.size.get_size(abs_size, rel_size)

        for x, c in zip(range(width + 1), self.text):
            pixels[(x, 0)] = c

        return pixels
