from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Generator
from typing import Union
from color import no_color, XTerm256NoColor

_regex_escape_code: str = r"(\x1b\[\d+(;\d+){0,2}m)*"
_regex_escape_code_char: str = "(" + _regex_escape_code + r"(\S)" + _regex_escape_code + r")|(\s)"
_regex_escape_code_word: str = _regex_escape_code + r"(\S+)" + _regex_escape_code


##
# FormatStr
##


def escaped_len(s: str):
    return len(without_escape_codes(s))


def just(s: str, width: int, mode: Optional[Literal["left", "right", "center"]], fill_char=" ") -> str:
    """
    this method aligns the string depending on the mode

    Parameters
    ----------
    s : str
        to be adjusted
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

    if escaped_len(fill_char) != 1:
        raise ValueError("the length of the fill_char must be 1")

    width = max(escaped_len(s), width)

    if mode == "left":
        s = s + fill_char * (width - escaped_len(s))
    elif mode == "right":
        s = fill_char * (width - escaped_len(s)) + s
    elif mode == "center":
        shift = (width - escaped_len(s)) // 2
        s = fill_char * shift + s + fill_char * (shift + (width - escaped_len(s)) % 2)
    else:
        raise ValueError(f"invalid mode: {mode}")

    return s


def words(s: str) -> Generator[str, None, None]:
    """
    splits a string into individual words. this method special escape characters aware

    Returns
    -------
    Iterator:
        an Generator yielding all words
    """
    for match in re.finditer(_regex_escape_code_word, s):
        yield s[match.start():match.end()]


def wrap(s: str, width: int) -> Generator[str, None, None]:
    """
    this method splits the formatted string into substrings of the specified length.
    if the specified width is smaller than every word, each line will contain only one word.

    Parameters
    ----------
    s : str
        the str to be splitted into words
    width : int
        the maximum width a substring may have

    Returns
    -------
    Iterable :
        each line is a new formatted string
    """
    word_list = list(words(s))
    line = []
    while word_list:
        word = word_list.pop(0)
        if escaped_len(" ".join(str(s) for s in [*line, word])) > width or word == "\n":
            if line:
                yield " ".join(str(s) for s in line)
            line = [word]
        else:
            line.append(word)
    yield " ".join(str(s) for s in line)


def without_escape_codes(s: str) -> str:
    """
    removes all formatted codes and returns a string containing only letters, whitespace characters,
    numbers and special characters. if the string does not contain any escape codes a new string
    with unchanged content will be returned

    Returns
    -------
    str:
        a string without escape codes
    """
    return re.sub(_regex_escape_code, "", s, 0)


def chars(s: str) -> Generator[str, None, None]:
    """
    splits a string into individual characters. this method special escape characters aware

    Returns
    -------
    Iterator:
        an Generator yielding all characters
    """
    for match in re.finditer(_regex_escape_code_char, s):
        yield s[match.start():match.end()]


def __tokenize(s: str) -> Generator[str, None, None]:
    """
    In development!!! very slow at the moment
    """
    pattern = re.compile(r"(?P<color_codes>\x1b\[\d+(;\d+){0,2}m)*(?P<char>.)")
    pattern_end = re.compile(r"(\x1b\[\d+(;\d+){0,2}m)*$")
    s_ = pattern_end.sub("", s)
    start_pos = 0
    while match := pattern.search(s_, start_pos):
        yield no_color() + s_[match.start():match.end()] + no_color()
        if match.group("color_codes") and (m := re.match(r"\x1b\[0m", match.group("color_codes"))):
            start_pos = match.end("char")
        else:
            s_ = s_[:match.start("char")] + s_[match.end("char"):]

        if s_.endswith("m"):
            s_ = pattern_end.sub("", s_)
