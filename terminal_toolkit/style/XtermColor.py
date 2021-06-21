import colorsys
import re
from dataclasses import dataclass, field
import webcolors
from typing import NamedTuple, Union, TypeVar

##
# regex strings used for parsing colors
##
regex_rgbColor = r'rgb\s?\((?P<red>\d{1,3}),\s?(?P<green>\d{1,3}),\s?(?P<blue>\d{1,3})\)'
regex_hslColor = r'hsl\s?\((?P<hue>\d{1,3})°?,\s?(?P<saturation>\d{1,3})%?,\s?(?P<lightness>\d{1,3})%?\)'
regex_cmykColor = r'cmyk\s?\((?P<cyan>\d{1,3})%?,\s?(?P<magenta>\d{1,3})%?,' \
                  r'\s?(?P<yellow>\d{1,3})%?,\s?(?P<key>\d{1,3})%?\)'
regex_hexColor = r'(?P<hex>#[0-9a-fA-F]+)'

##
# proxy datatype
##
RGB = NamedTuple("RGB", [("red", int), ("green", int), ("blue", int)])
HSL = NamedTuple("HSL", [("hue", int), ("saturation", float), ("lightness", float)])
CMYK = NamedTuple("CMYK", [("cyan", float), ("magenta", float), ("yellow", float), ("key", float)])
HEX = type("HEX", (str,), {"__repr__": lambda self: f'HEX={self}'})
T = TypeVar("T")


##
# helper functions
##

def clamp(x: T, minimum: T = 0, maximum: T = 1) -> T:
    """return a value within min and max"""
    return max(minimum, min(x, maximum))


##
# functions for converting colors
# the basic idea is, that a string is parsed, that converted into rgb values
# which then can be converted into any other color format (e.g hsl, hex, ..)
##

def color_to_rgb(color: str) -> RGB:
    color = color.strip().lower()
    if rgb := re.match(regex_rgbColor, color):
        r, g, b = int(rgb.group("red")), int(rgb.group("green")), int(rgb.group("blue"))
    elif hsl := re.match(regex_hslColor, color):
        r, g, b = hsl_to_rgb((int(hsl.group("hue")),
                              int(hsl.group("saturation")),
                              int(hsl.group("lightness"))))
    elif _hex := re.match(regex_hexColor, color):
        r, g, b = webcolors.hex_to_rgb(_hex.group("hex"))
    elif cmyk := re.match(regex_cmykColor, color):
        r, g, b = cmyk_to_rgb((int(cmyk.group("cyan")),
                               int(cmyk.group("magenta")),
                               int(cmyk.group("yellow")),
                               int(cmyk.group("key"))))

    else:
        try:
            r, g, b = webcolors.name_to_rgb(color)
        except ValueError as e:
            r, g, b = 255, 255, 255

    return r, g, b


def rgb_to_xterm_256(rgb: RGB) -> int:
    r, g, b = rgb

    if r == g == b:
        return 16 if sum([r, g, b]) < 24 else (
            231 if sum([r, g, b]) > 744 else int(round((float(r - 8) / 247) * 24) + 232))
    else:
        return int(
            16 + (36 * round(float(r) / 255 * 5)) + (6 * round(float(g) / 255 * 5)) + round(float(b) / 255 * 5))


def rgb_to_cmyk(rgb: RGB) -> CMYK:
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


def cmyk_to_rgb(cmyk: CMYK) -> RGB:
    c, m, y, k = cmyk

    r = 255 * (1.0 - c / 100.0) * (1.0 - k / 100.0)
    g = 255 * (1.0 - m / 100.0) * (1.0 - k / 100.0)
    b = 255 * (1.0 - y / 100.0) * (1.0 - k / 100.0)
    return round(r), round(g), round(b)


def rgb_to_hsl(rgb: RGB) -> HSL:
    r, g, b = rgb

    r, g, b = [x / 255 for x in [r, g, b]]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return round(h * 360), round(s, 2), round(l, 2)


def hsl_to_rgb(hsl: HSL) -> RGB:
    h, s, l = hsl

    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    r, g, b = [int(x * 255) for x in [r, g, b]]
    return r, g, b


##
# dataclass for storing color information
##


XTerm256NoColor = "\u001b[0m"


@dataclass(frozen=True, eq=True)
class XTerm256Color:
    """this object stores and converts colors. the different color formats can be accessed via the public attributes
    of the object. if one of these attributes is changed, all others are updated with the new color. the default
    color is white """

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
            return get_color(f'hsl({round(h)},{round(s * 100)},{round(clamp(l + other) * 100)})')
        elif isinstance(other, XTerm256Color):
            r, g, b = [clamp(round((x[0] + x[1]) / 2), minimum=0, maximum=255) for x in zip(self.RGB, other.RGB)]
            return get_color(f'rgb({r},{g},{b})')
        else:
            raise TypeError(f'unsupported operand type(s) for +: Color and {type(other)}')

    def __sub__(self, other):
        """By subtracting a number, the color can be made darker.
        Also to calculate the difference between two colors, the difference can be calculated in this way.
        Due to rounding errors, the process may not be able to be reversed identically."""
        if isinstance(other, (int, float)):
            h, s, l = self.HSL
            return get_color(f'hsl({round(h)},{round(s * 100)}%,{round(clamp(l - other) * 100)}%)')
        elif isinstance(other, XTerm256Color):
            r, g, b = [clamp(round((x[0] - x[1]) / 2), minimum=0, maximum=255) for x in zip(self.RGB, other.RGB)]
            return get_color(f'rgb({r},{g},{b})')
        else:
            raise TypeError(f'unsupported operand type(s) for -: Color and {type(other)}')


##
# interface method (these are the one the developer actual uses)
##


def get_color(color: Union[RGB, str]) -> XTerm256Color:
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
    >>> white = get_color("#ffffff")
    >>> black = get_color("black")
    >>> print(foreground_color(white) +
    ...         background_color(black) +
    ...         "this is white text on a black background" +
    ...         XTerm256NoColor)

    Parameters
    ----------
    color : str or RGB
        this either must be a tuple containing rgb values or a string with color information.

    See Also
    --------
    foreground_color : returns a string that can be used to color the text (the foreground)
    background_color : returns a string that can be used to color the background
    lighten_color : returns the next brighter shade for the given color
    darken_color: returns the next darker shade for the given color
    all_color_shades : return all possible shades for the given color

    Returns
    -------
    XTerm256Color :
        a color that stored the color information.
    """

    r, g, b = color if isinstance(color, RGB) else color_to_rgb(color)

    try:
        name = webcolors.rgb_to_name((r, g, b))
    except ValueError:
        name = "not defined"

    return XTerm256Color(
        RGB=RGB(r, g, b),
        HEX=HEX(webcolors.rgb_to_hex((r, g, b))),
        HSL=HSL(*rgb_to_hsl((r, g, b))),
        CMYK=CMYK(*rgb_to_cmyk((r, g, b))),
        NAME=name,
        X_TERM=f"\u001b[38;5;{rgb_to_xterm_256((r, g, b))}m",
        X_TERM_BACKGROUND=f"\u001b[48;5;{rgb_to_xterm_256(RGB(r, g, b))}m"
    )


def foreground_color(xterm_color: XTerm256Color) -> str:
    """
    This function returns a str that can be printed before the actual string containing the text.
    By doing this you will color the text (the foreground) by the color value stored in the xterm_color.
    To disable the color print 'XTerm256NoColor'.

    Parameters
    ----------
    xterm_color : XTerm256Color
        the color of the text

    See Also
    --------
    background_color : returns a string that can be used to color the background

    Returns
    -------
    str :
        An escape string that changes the foreground color of the terminal for the following characters.
    """
    return xterm_color.X_TERM


def background_color(xterm_color: XTerm256Color) -> str:
    """
    This function returns a str that can be printed before the actual string containing the text.
    By doing this you will color the background by the color value stored in the xterm_color.
    To disable the color print 'XTerm256NoColor'.

    Parameters
    ----------
    xterm_color : XTerm256Color
        the color of the background

    See Also
    --------
    foreground_color : returns a string that can be used to color the text (the foreground)

    Returns
    -------
    str :
        An escape string that changes the background color of the terminal for the following characters.
    """
    return xterm_color.X_TERM_BACKGROUND


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
