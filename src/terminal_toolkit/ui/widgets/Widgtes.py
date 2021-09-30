from abc import ABC
from dataclasses import dataclass, field
from typing import AnyStr, final

from src.terminal_toolkit.ui.events import Events
from src.terminal_toolkit.ui.widgets.BaseClasses import BaseWidget


@dataclass
class Widget(BaseWidget, ABC):

    @final
    def handle_event(self, event: Events.Event):
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
