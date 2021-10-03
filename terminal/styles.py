from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass, field
from typing import Literal, Optional, Generator
from typing import NamedTuple, TypeVar
from typing import Union

import webcolors

##
# regex strings used for parsing colors
##
_regex_rgbColor = r'rgb\s?\((?P<red>\d{1,3}),\s?(?P<green>\d{1,3}),\s?(?P<blue>\d{1,3})\)'
_regex_hslColor = r'hsl\s?\((?P<hue>\d{1,3})°?,\s?(?P<saturation>\d{1,3})%?,\s?(?P<lightness>\d{1,3})%?\)'
_regex_cmykColor = r'cmyk\s?\((?P<cyan>\d{1,3})%?,\s?(?P<magenta>\d{1,3})%?,' \
                   r'\s?(?P<yellow>\d{1,3})%?,\s?(?P<key>\d{1,3})%?\)'
_regex_hexColor = r'(?P<hex>#[0-9a-fA-F]+)'

##
# regx strings used for escaped strings
##
_regex_escape_code: str = r"(\u001b\[\d+(;\d+){0,2}m)*"
_regex_escape_code_char: str = "(" + _regex_escape_code + r"(\S)" + _regex_escape_code + r")|(\s)"
_regex_escape_code_word: str = _regex_escape_code + r"(\S+)" + _regex_escape_code

##
# proxy datatype
##
RGB = NamedTuple("RGB", [("red", int), ("green", int), ("blue", int)])
HSL = NamedTuple("HSL", [("hue", int), ("saturation", float), ("lightness", float)])
CMYK = NamedTuple("CMYK", [("cyan", float), ("magenta", float), ("yellow", float), ("key", float)])
HEX = type("HEX", (str,), {"__repr__": lambda self: f'HEX={self}'})
T = TypeVar("T")
number = Union[int, float]


##
# helper functions
##

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


##
# functions for converting colors
# the basic idea is, that a string is parsed, that converted into rgb values
# which then can be converted into any other color format (e.g hsl, hex, ..)
##


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


##
# color functions
##

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


##
# dataclass for storing color information
##

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


##
# helper methods
##


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


##
# FormatStr
##

@dataclass(frozen=True, init=False)
class FormatStr:
    s: str

    def __init__(self, s: Union[str, FormatStr]):
        """
        creates new FormatStr

        Examples
        --------
        >>> s = FormatStr("{red:c}Red Color{nocolor}{rgb(0, 0, 255):bg}Blue Background")
        >>> print(s)

        Parameters
        ----------
        s : str
            the string to be comverted to a FormatStr
        """
        if isinstance(s, str) and s != "":
            s += str(XTerm256NoColor())
        elif isinstance(s, FormatStr):
            s = s.s
        else:
            raise ValueError(f"invalid type for parameter 's': {type(s)}")
        super(FormatStr, self).__setattr__("s", s)

    def __eq__(self, other: Union[str, FormatStr]):
        if isinstance(other, str):
            return other == self.s
        elif isinstance(other, FormatStr):
            return other.s == self.s
        else:
            raise ValueError(f"invalid type for comparison: {type(other)}")

    def __len__(self):
        return len(self.without_escape_codes())

    def __str__(self):
        return self.s
    
    def __repr__(self):
        return f"FormatStr(s='{str(self)}')"

    def __contains__(self, item: Union[str, FormatStr]) -> bool:
        """
        use: "test" in s

        Parameters
        ----------
        item : str
            will be tested

        Returns
        -------
        bool:
            true if item is a string or formatted string an a subsequence of this formatted string
        """
        if isinstance(item, FormatStr):
            return item.s in self.s
        elif isinstance(item, str):
            return item in self.s
        else:
            return False

    def __add__(self, other) -> FormatStr:
        """
        allows the concatenation of two strings. it is possible to combine two formatted strings, an formatted string
        with a str and also a str with an formatted str (see __radd__). if an formatted string is concatenated with a
        str, the styles are inherited from the formatted string. if two formatted strings are joined, the style of the
        first formatted string is inherited.

        Parameters
        ----------
        other:
            will be joined with this formatted string

        Returns
        -------
        EscapedStr:
            because formatted strings are immutable, a new formatted string is generated and returned by this method
        """
        if isinstance(other, FormatStr):
            return FormatStr(self.s + other.s)
        elif isinstance(other, str):
            return FormatStr(self.s + other)
        else:
            raise TypeError(f"can only concatenate FormatStr (not '{type(other).__name__}') to FormatStr")

    def __radd__(self, other) -> FormatStr:
        """
        allows the concatenation of two strings. it is possible to combine two formatted strings, an formatted string
        with a str and also a str with an formatted str. if an formatted string is concatenated with a
        str, the styles are inherited from the formatted string. if two formatted strings are joined, the style of the
        first formatted string is inherited.

        Parameters
        ----------
        other:
            will be joined with this formatted string

        Returns
        -------
        EscapedStr:
            because formatted strings are immutable, a new formatted string is generated and returned by this method
        """
        if isinstance(other, str):
            return FormatStr(other + self.s)
        elif isinstance(other, FormatStr):
            return FormatStr(other.s + self.s)
        else:
            raise TypeError(f"can only concatenate FormatStr (not '{type(other).__name__}') to FormatStr")

    def just(self, width: int, mode: Optional[Literal["left", "right", "center"]], fill_char=" ") -> FormatStr:
        """
        this method aligns the string depending on the mode

        Parameters
        ----------
        width: int
            the string is adjusted to this width
        mode: str
            the string is adjusted according to the mode specified here. the mode defined in the stylesheet is always
            used first. if no mode is declared in the stylesheet, the mode must be passed directly to the method

        fill_char: str
            if the length of the string is shorter than the specified width, the string is padded with this character

        Returns
        -------
        str:
            a new formatted string which now has exactly the same length as the specified width. the additional places
            were filled up with the fill_char. the new formatted string inherits the style of this formatted string

        Raises
        ------
        ValueError
            is raised if the length of this formatted string is bigger that the specified width
        ValueError
            is raised if the length of the fill_char is not one

        """

        if len(FormatStr(fill_char)) != 1:
            raise ValueError("the length of the fill_char must be 1")

        width = max(len(self), width)

        if mode == "left":
            s = self.s + fill_char * (width - len(self))
        elif mode == "right":
            s = fill_char * (width - len(self)) + self.s
        elif mode == "center":
            shift = (width - len(self)) // 2
            s = fill_char * shift + self.s + fill_char * (shift + (width - len(self)) % 2)
        else:
            raise ValueError(f"invalid mode: {mode}")

        return FormatStr(s)

    def wrap(self, width: int) -> Generator[FormatStr, None, None]:
        """
        this method splits the formatted string into substrings of the specified length.
        if the specified width is smaller than every word, each line will contain only one word.

        Parameters
        ----------
        width : int
            the maximum width a substring may have

        Returns
        -------
        Iterable :
            each line is a new formatted string
        """
        words = list(self.to_words())
        line = []
        while words:
            word = words.pop(0)
            if len(FormatStr(" ".join(str(s) for s in [*line, word]))) > width or word == "\n":
                if line:
                    yield FormatStr(" ".join(str(s) for s in line))
                line = [word]
            else:
                line.append(word)
        yield FormatStr(" ".join(str(s) for s in line))

    def without_escape_codes(self) -> str:
        """
        removes all formatted codes and returns a string containing only letters, whitespace characters,
        numbers and special characters. if the string does not contain any escape codes a new string
        with unchanged content will be returned

        Returns
        -------
        str:
            a string without escape codes
        """
        return re.sub(_regex_escape_code, "", self.s, 0)

    def __iter__(self) -> Generator[str, None, None]:
        """
        splits a string into individual characters. this method special escape characters aware

        Returns
        -------
        Iterator:
            an Generator yielding all characters
        """
        for match in re.finditer(_regex_escape_code_char, self.s):
            yield self.s[match.start():match.end()]

    def to_words(self) -> Generator[FormatStr, None, None]:
        """
        splits a string into individual words. this method special escape characters aware

        Returns
        -------
        Iterator:
            an Generator yielding all words
        """
        for match in re.finditer(_regex_escape_code_word, self.s):
            yield FormatStr(self.s[match.start():match.end()])
