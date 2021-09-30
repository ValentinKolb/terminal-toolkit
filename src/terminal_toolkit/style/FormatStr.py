from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Union

regex_escape_code_char: str = r"(?P<escaped_character>(\x1b\[\d+(;\d+){0,2}m)+(\s|\S)?)|" \
                              r"(?P<whitespace_character>\s)|" \
                              r"(?P<word_character>\S)"
regex_escape_code: str = r"(?P<escaped_character>(\x1b\[\d+(;\d+){0,2}m))"
regex_escape_code_word: str = r"(?P<escaped_word>(\x1b\[\d+(;\d+){0,2}m)+\S+ ?)|" \
                              r"(?P<whitespace_character>\s)|" \
                              r"(?P<word_characters>\S+ ?)"


def remove_escape_codes(s: str, lower: bool = False, _strip: bool = False) -> str:
    """
    removes all formatted codes and returns a string containing only letters, whitespace characters,
    numbers and special characters. if the string does not contain any escape codes a new string
    with unchanged content will be returned

    Parameters
    ----------
    lower : bool
        if true, s will be converted to all lowercase
    _strip : bool
        if True, all leading and trailing whitespaces will be removed
    s : str
        will be cleaned

    Returns
    -------
    str:
        a new string without escape codes
    """
    s = re.sub(regex_escape_code, "", s, 0)

    if lower:
        s = s.lower()
    if _strip:
        s = s.strip()
    return s


def split_into_words(s: str) -> tuple[str]:
    """
    splits a string into individual split_into_words. this method special escape characters aware

    Parameters
    ----------
    s : str
        will be split into single words

    Returns
    -------
    tuple:
        a tuple containing all words
    """
    words = []
    while match := re.match(regex_escape_code_word, s):
        words.append(str(s[match.start():match.end()]))
        s = re.sub(regex_escape_code_word, "", s, count=1)
    return tuple(words)


@dataclass(frozen=True, init=False)
class FormatStr:
    s: str

    def __init__(self, s: Union[str, FormatStr]):
        super(FormatStr, self).__setattr__("s", s if isinstance(s, str) else s.s)

    def __format__(self, format_spec):
        pass

    def __len__(self):
        return sum(1 for _ in re.finditer(regex_escape_code_char, self.s))

    def __str__(self):
        return ""

    def __contains__(self, item: Union[str, EscapedStr]) -> bool:
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
        if isinstance(item, EscapedStr):
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
        elif isinstance(other, EscapedStr):
            return FormatStr(other.s + self.s)
        else:
            raise TypeError(f"can only concatenate FormatStr (not '{type(other).__name__}') to FormatStr")

    def __iter__(self, pattern=regex_escape_code_char) -> str:
        """
        this methods allows that an formatted string is used as an iterable

        Parameters
        ----------
        pattern : str
            a regular expression pattern that determines which group of letters is returned

        Returns
        -------
        str:
            this method returns character by character stored in this string, but all escape characters preceding a
            character are returned with that character
        """
        s = str(self)
        while match := re.match(pattern, s):
            yield s[match.start():match.end()]
            s = re.sub(pattern, "", s, count=1)


class EscapedStr:
    """
    a string like object that provides additional functionality for working with escape codes and css styles

    Attributes
    ----------
    WORDS: tuple
        all split_into_words as iterable that are contained in the formatted string

    STYLE: CSS_Style:
        an optional style object that allows you to give this string css style like appearance
    """

    _s: str

    def just(self, width: int, mode: Optional[Literal["left", "right", "center"]] = None, fill_char=" ") -> EscapedStr:
        """
        this method aligns the escape string depending on the mode

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
            were filled up with the fillchar. the new formatted string inherits the style of this formatted string

        Raises
        ------
        StyleError
            is raised if the length of this formatted string is bigger that the specified width
        StyleError
            is raised if the mode is neither specified in the stylesheet nor passed
        StyleError
            is raised if the length of the fillchar is not one

        """
        s = self._s
        mode = self.STYLE.TEXT.TEXT_ALIGN if self.STYLE else mode

        if not mode:
            raise StyleError("missing parameter mode: "
                             "the mode must either be specified in the stylesheet or passed to the method")
        elif len(self) > width:
            raise StyleError("invalid value range for parameter width: "
                             "specify a width that is at least as long as the formatted string")
        elif EscapedStr.length(fill_char) != 1:
            raise StyleError()

        if mode == "left":
            s = s + fill_char * (width - len(self))
        elif mode == "right":
            s = fill_char * (width - len(self)) + s
        elif mode == "center":
            shift = (width - len(self)) // 2
            s = fill_char * shift + s + fill_char * shift
        return EscapedStr(s, self.STYLE)

    def wrap(self, width: int, replace_taps=4) -> tuple[EscapedStr]:
        """
        this method splits the formatted string into substrings of the specified length. split_into_words are not split.
        if a word is longer than the specified length, the rest of the word is cut off

        Parameters
        ----------
        width: int
            the maximum width a substring may have
        replace_taps: int
            the number of whitespaces to replace a tab with

        Returns
        -------
            a tuple of lines. each line is a new formatted string, which has inherited the style of this formatted string
        """
        s = self._s.expandtabs(replace_taps)
        words = list(EscapedStr(s).WORDS)
        line = str()
        lines: list[EscapedStr] = []
        while words:
            word = words.pop(0)
            if len(EscapedStr(line + word, self.STYLE)) > width or word == "\n":
                lines.append(EscapedStr(line, self.STYLE))
                line = word[0:width] if word != "\n" else str()
            else:
                line += word
        lines.append(EscapedStr(line, self.STYLE))
        return tuple(lines)

    def raw_str(self) -> str:
        """
        removes all formatted codes and returns a string containing only letters, whitespace characters,
        numbers and special characters. if the string stored in this formatted str does not contain any
        escape codes a new string with the same content as this formatted str will be returned

        Returns
        -------
        str:
            the cleaned character string
        """
        return remove_escape_codes(self._s)

    def __iter__(self, pattern=regex_escape_code_char) -> str:
        """
        this methods allows that an formatted string is used as an iterable

        Parameters
        ----------
        pattern : str
            a regular expression pattern that determines which group of letters is returned

        Returns
        -------
        str:
            this method returns character by character stored in this string, but all escape characters preceding a
            character are returned with that character
        """
        s = str(self)
        while match := re.match(pattern, s):
            yield s[match.start():match.end()]
            s = re.sub(pattern, "", s, count=1)

    def __str__(self) -> str:
        """
        returns the string stored in this formatted string. If a style was defined for this formatted string,
        it will be applied here

        Returns
        -------
        str:
            a string that contains all style attributes defined the stylesheet in the form of escape codes

        """

        def _get_char(char: str, font_family: str):
            return styles_and_symbols.UNICODE_FONTS.get(font_family, {}).get(char, char)

        if isinstance(self.STYLE, CSS_Style):
            if "uppercase" in self.STYLE.TEXT.TEXT_TRANSFORM:
                s = self.raw_str().upper()
            elif "lowercase" in self.STYLE.TEXT.TEXT_TRANSFORM:
                s = self.raw_str().lower()
            elif "capitalize" in self.STYLE.TEXT.TEXT_TRANSFORM:
                s = self.raw_str().title()
            else:
                s = self.raw_str()
            style = self.STYLE.COLOR.X_TERM + self.STYLE.BACKGROUND_COLOR.X_TERM_BACKGROUND + \
                    styles_and_symbols.get_font_style(self.STYLE.TEXT.TEXT_DECORATION) + \
                    styles_and_symbols.get_font_style(self.STYLE.FONT.FONT_WEIGHT)
            new_string = ""
            for c in s:
                new_string += style + _get_char(c, self.STYLE.FONT.FONT_FAMILY) + styles_and_symbols.RESET
            return new_string

        else:
            return self.raw_str()
