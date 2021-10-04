from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass, field
from typing import NamedTuple, TypeVar, Union

import webcolors

_regex_rgbColor = r'rgb\s?\((?P<red>\d{1,3}),\s?(?P<green>\d{1,3}),\s?(?P<blue>\d{1,3})\)'
_regex_hslColor = r'hsl\s?\((?P<hue>\d{1,3})°?,\s?(?P<saturation>\d{1,3})%?,\s?(?P<lightness>\d{1,3})%?\)'
_regex_cmykColor = r'cmyk\s?\((?P<cyan>\d{1,3})%?,\s?(?P<magenta>\d{1,3})%?,' \
                   r'\s?(?P<yellow>\d{1,3})%?,\s?(?P<key>\d{1,3})%?\)'
_regex_hexColor = r'(?P<hex>#[0-9a-fA-F]+)'
RGB = NamedTuple("RGB", [("red", int), ("green", int), ("blue", int)])
HSL = NamedTuple("HSL", [("hue", int), ("saturation", float), ("lightness", float)])
CMYK = NamedTuple("CMYK", [("cyan", float), ("magenta", float), ("yellow", float), ("key", float)])
HEX = type("HEX", (str,), {"__repr__": lambda self: f'HEX={self}'})
T = TypeVar("T")
number = Union[int, float]


def _clamp(x: T, minimum: T = 0, maximum: T = 1) -> T:
    """return a value within min and max"""
    return max(minimum, min(x, maximum))


def _normalize(value: number, value_range: tuple[number, number]) -> float:
    """
    normalizes a value in between a scale

    Parameters
    ----------
    value :
        the value to be normalized
    value_range :
        the scale

    Returns
    -------
    number :
        a value between 0 and 1
    """
    return _clamp((value - min(*value_range)) / (max(*value_range) - min(*value_range)))


def _rgb_to_xterm_256(rgb: RGB) -> int:
    r, g, b = rgb

    if r == g == b:
        return 16 if sum([r, g, b]) < 24 else (
            231 if sum([r, g, b]) > 744 else int(round((float(r - 8) / 247) * 24) + 232))
    else:
        return int(
            16 + (36 * round(float(r) / 255 * 5)) + (6 * round(float(g) / 255 * 5)) + round(float(b) / 255 * 5))


def _rgb_to_cmyk(rgb: RGB) -> CMYK:
    r, g, b = rgb

    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100
    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255
    min_cmy = min(c, m, y)
    return round((c - min_cmy) / (1 - min_cmy), 2), round((m - min_cmy) / (1 - min_cmy), 2), round(
        (y - min_cmy) / (
                1 - min_cmy), 2), round(min_cmy, 2)


def _cmyk_to_rgb(cmyk: CMYK) -> RGB:
    c, m, y, k = cmyk

    r = 255 * (1.0 - c / 100.0) * (1.0 - k / 100.0)
    g = 255 * (1.0 - m / 100.0) * (1.0 - k / 100.0)
    b = 255 * (1.0 - y / 100.0) * (1.0 - k / 100.0)
    return round(r), round(g), round(b)


def _rgb_to_hsl(rgb: RGB) -> HSL:
    r, g, b = rgb

    r, g, b = [x / 255 for x in [r, g, b]]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return round(h * 360), round(s, 2), round(l, 2)


def _hsl_to_rgb(hsl: HSL) -> RGB:
    h, s, l = hsl

    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    r, g, b = [int(x * 255) for x in [r, g, b]]
    return r, g, b


def no_color() -> str:
    return str(XTerm256NoColor())


def color(color_value: str) -> XTerm256Color:
    """
    This function takes a string containing color information or rgb values and turns that into a xterm color.
    This color object can then be used to color the output to the terminal.

    Supported Color Formats
    -----------------------
        - the name of the color e.g. 'white', 'orange', ...
        - rgb(red,green,blue) e.g. rgb(255,255,255)
        - hsl(hue,saturation,luminance) e.g. hsl(1,2,3)
        - cmyk(cyan,magenta,yellow,key) e.g. cmyk(1,2,3,4)
        - hex e.g. #ffffff

    Usage
    -----
    >>> white = color("#ffffff")
    >>> black = color("black")
    >>> print(white.X_TERM +
    ...         black.X_TERM_BACKGROUND +
    ...         "this is white text on a black background" +
    ...         str(XTerm256NoColor))

    Parameters
    ----------
    color_value : str or RGB
        this either must be a tuple containing rgb values or a string with color information.

    See Also
    --------
    foreground_color : returns a string that can be used to color the text (the foreground)
    background_color : returns a string that can be used to color the background
    lighten_color : returns the next brighter shade for the given color
    darken_color: returns the next darker shade for the given color
    all_color_shades : return all possible shades for the given color

    Raises
    ------
    ValueError :
        if the color can't be converted

    Returns
    -------
    XTerm256Color :
        a color that stored the color information.
    """

    color_value = color_value.strip().lower()
    if rgb_match := re.match(_regex_rgbColor, color_value):
        r, g, b = int(rgb_match.group("red")), \
                  int(rgb_match.group("green")), \
                  int(rgb_match.group("blue"))
    elif hsl_match := re.match(_regex_hslColor, color_value):
        r, g, b = _hsl_to_rgb((int(hsl_match.group("hue")),
                               int(hsl_match.group("saturation")),
                               int(hsl_match.group("lightness"))))
    elif hex_match := re.match(_regex_hexColor, color_value):
        r, g, b = webcolors.hex_to_rgb(hex_match.group("hex"))
    elif cmyk_match := re.match(_regex_cmykColor, color_value):
        r, g, b = _cmyk_to_rgb((int(cmyk_match.group("cyan")),
                                int(cmyk_match.group("magenta")),
                                int(cmyk_match.group("yellow")),
                                int(cmyk_match.group("key"))))

    else:
        try:
            r, g, b = webcolors.name_to_rgb(color_value)
        except ValueError as _:
            raise ValueError(f'unable to convert color for value: {color_value}')

    return rgb(r, g, b)


def rgb(red: int, green: int, blue: int) -> XTerm256Color:
    try:
        name = webcolors.rgb_to_name((red, green, blue))
    except ValueError:
        name = "not defined"

    return XTerm256Color(
        RGB=RGB(red, green, blue),
        HEX=HEX(webcolors.rgb_to_hex((red, green, blue))),
        HSL=HSL(*_rgb_to_hsl((red, green, blue))),
        CMYK=CMYK(*_rgb_to_cmyk((red, green, blue))),
        NAME=name,
        X_TERM=f"\u001b[38;5;{_rgb_to_xterm_256((red, green, blue))}m",
        X_TERM_BACKGROUND=f"\u001b[48;5;{_rgb_to_xterm_256(RGB(red, green, blue))}m"
    )


def hsl(hue: int, saturation: float, lightness: float) -> XTerm256Color:
    return rgb(*_hsl_to_rgb(HSL(hue, saturation, lightness)))


def cmyk(cyan: float, magenta: float, yellow: float, key: float) -> XTerm256Color:
    return rgb(*_cmyk_to_rgb(CMYK(cyan, magenta, yellow, key)))


def hex_(value: str) -> XTerm256Color:
    return rgb(*webcolors.hex_to_rgb(value))


@dataclass(frozen=True)
class XTerm256NoColor:

    def __str__(self):
        return "\u001b[0m"


@dataclass(frozen=True, eq=True)
class XTerm256Color:
    """
    this object stores and converts colors. the different color formats can be accessed via the public attributes
    of the object.

    To create a color use the factory methods: rgb(), hsl(), hex_(), cmyk() or color(), no_color()

    To use the color when printing, use the format method or a f-string (see examples below=

    Examples
    --------
    >>> red = color("red")
    >>> green = rgb(0, 255, 0)
    >>> blue = hex_("#0000ff")
    >>> print(f'{red:c}Red Text{no_color()}No Color{green:bg}{blue:c}Green Background and Blue Text{no_color()}')
    """

    RGB: RGB = field(compare=True)
    HEX: HEX = field(compare=False)
    HSL: HSL = field(compare=False)
    CMYK: CMYK = field(compare=False)
    NAME: str = field(compare=False)
    X_TERM: str = field(compare=False)
    X_TERM_BACKGROUND: str = field(compare=False)

    def __repr__(self):
        return f'[{self.X_TERM}#{XTerm256NoColor}{self.X_TERM_BACKGROUND}#{XTerm256NoColor}]' \
               f' {self.__class__.__name__}: {self.NAME}, {self.RGB}, {self.HSL}, {self.CMYK}, {repr(self.HEX)}'

    def __add__(self, other):
        """By adding a number the color can be made brighter.
        Also to mix two colors you can add them together.
        Due to rounding errors, the process may not be able to be reversed identically."""
        if isinstance(other, (int, float)):
            h, s, l = self.HSL
            return color(f'hsl({round(h)},{round(s * 100)},{round(_clamp(l + other) * 100)})')
        elif isinstance(other, XTerm256Color):
            r, g, b = [_clamp(round((x[0] + x[1]) / 2), minimum=0, maximum=255) for x in zip(self.RGB, other.RGB)]
            return color(f'rgb({r},{g},{b})')
        else:
            raise TypeError(f'unsupported operand type(s) for +: Color and {type(other)}')

    def __sub__(self, other):
        """By subtracting a number, the color can be made darker.
        Also to calculate the difference between two colors, the difference can be calculated in this way.
        Due to rounding errors, the process may not be able to be reversed identically."""
        if isinstance(other, (int, float)):
            h, s, l = self.HSL
            return color(f'hsl({round(h)},{round(s * 100)}%,{round(_clamp(l - other) * 100)}%)')
        elif isinstance(other, XTerm256Color):
            r, g, b = [_clamp(round((x[0] - x[1]) / 2), minimum=0, maximum=255) for x in zip(self.RGB, other.RGB)]
            return color(f'rgb({r},{g},{b})')
        else:
            raise TypeError(f'unsupported operand type(s) for -: Color and {type(other)}')

    def __format__(self, format_spec):

        result = ""

        for format_ in (s for s in format_spec.split("+") if s):
            format_: str = format_.lower().strip()
            if format_ in ("c", "color"):
                result += self.X_TERM
            elif format_ in ("bg", "background"):
                result += self.X_TERM_BACKGROUND
            else:
                raise ValueError(f'invalid format spec: {format_!r}')

        return result

    def __iter__(self):
        """
        Returns
        -------
        RGB :
            returns the red, green and blue value of the color
        """
        yield from self.RGB


def lighten_color(xterm_color: XTerm256Color) -> XTerm256Color:
    """
    This function takes an xterm_color and returns the next brighter shade of it. The advantage of using this method
    if contrast to create an other color with a technically 'brighter' rgb value (or hsl, hex, ..) is, that often
    a whole range of rgb values (or hsl, hex, ..) is merged into one single xterm_color. This is the case, because
    only 256 different color exist (in contrast to the 16.777.216 possible RGB colors).

    Parameters
    ----------
    xterm_color : XTerm256Color
        the xterm_color

    See Also
    --------
    darken_color : returns the next darker shade
    all_color_shades : return all possible shades for the given color

    Returns
    -------
    XTerm256Color :
        the next brighter shade. if the color is already white, the color itself is returned
    """
    temp = xterm_color
    while temp.NAME != "white":
        temp = temp + 0.1
        if temp.X_TERM != xterm_color.X_TERM:
            break
    return temp


def darken_color(xterm_color: XTerm256Color) -> XTerm256Color:
    """
    This function takes an xterm_color and returns the next darker shade of it. The advantage of using this method
    if contrast to create an other color with a technically 'darker' rgb value (or hsl, hex, ..) is, that often
    a whole range of rgb values (or hsl, hex, ..) is merged into one single xterm_color. This is the case, because
    only 256 different color exist (in contrast to the 16.777.216 possible RGB colors).

    Parameters
    ----------
    xterm_color : XTerm256Color
        the xterm_color

    See Also
    --------
    lighten_color : returns the next lighter shade
    all_color_shades : return all possible shades for the given color

    Returns
    -------
    XTerm256Color :
        the next darker shade. if the color is already black, the color itself is returned
    """
    temp = xterm_color
    while temp.NAME != "black":
        temp = temp - 0.1
        if temp.X_TERM != xterm_color.X_TERM:
            break
    return temp


def all_color_shades(xterm_color: XTerm256Color) -> list[XTerm256Color]:
    """
    This function takes an xterm_color as argument and returns all possible shades for this color.

    Parameters
    ----------
    xterm_color : XTerm256Color
        the color

    See Also
    --------
    lighten_color : returns the next brighter shade for the given color
    darken_color: returns the next darker shade for the given color

    Returns
    -------
    list:
        a list containing all color shades
    """
    temp = xterm_color
    darker = []
    while temp != temp.darken():
        darker.insert(0, temp.lighten())
        temp = temp.darken()

    temp = xterm_color
    brighter = []
    while temp != temp.lighten():
        brighter.append(temp.lighten())
        temp = temp.lighten()

    return darker + [xterm_color] + brighter


def color_scale(value: float, domain: tuple[float, float],
                color_range: tuple[XTerm256Color, XTerm256Color]) -> XTerm256Color:
    """
    Interpolates a color to match the value in the specified scale.
    If the value is smaller or larger then the domain, the boundaries of the domain will be used as value.

    Examples
    --------
    >>> white, black = color("white"), color("black")
    >>>
    >>> color_scale(0, (0,1), (white, black))  # will return white
    >>> color_scale(-1,(0,1), (white, black))  # will also return white
    >>>
    >>> color_scale(1, (0,1), (white, black))  # will return black
    >>> color_scale(2, (0,1), (white, black))  # will also return black
    >>>
    >>> color_scale(.5,(0,1), (white, black))  # will return the color in between white and black (~ gray)

    Parameters
    ----------
    value :
        the value translated to the corresponding color shade
    domain :
        the range of the value
    color_range :
        the two colors to be interpolated.

    Returns
    -------
    XTerm256Color :
        the interpolated color
    """

    v = _normalize(value, domain)
    (r1, g1, b1), (r2, g2, b2) = color_range
    r = (1 - v) * r1 + v * r2
    g = (1 - v) * g1 + v * g2
    b = (1 - v) * b1 + v * b2
    return rgb(int(r), int(g), int(b))