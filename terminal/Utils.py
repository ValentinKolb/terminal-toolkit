from typing import Callable

from terminal.Events import MODIFIER_KEYS
from terminal import *


def printf(*args, end="\n"):
    """
    todo

    Parameters
    ----------
    args

    Returns
    -------

    """
    print(*args, end=end, flush=True)


def delete_printed(num_chars: int):
    """
    this function deletes printed output. it is able to delete the last n chars printed to the terminal

    Parameters
    ----------
    num_chars : int
        the number of characters to be deleted
    """
    width, _ = get_size()
    _, cursor_col = get_cursor_pos()

    move_cursor_left(min(cursor_col - 1, num_chars))
    erase_end_of_line()
    num_chars -= cursor_col

    while num_chars > 0:
        set_title(f'{width=} {cursor_col=} {num_chars=}')
        getch()

        move_cursor_up()
        if width > num_chars:
            move_cursor_right(width - num_chars - 1)
        num_chars -= width
        erase_end_of_line()
    set_title(f'{width=} {cursor_col=} {num_chars=}')


def read(prompt: str, default: str = None, hide_input: bool = False, allowed_options: list = None):
    prompt = prompt.rstrip().removesuffix(":")

    if default:
        printf(f'{prompt} [{default}]', end=" : ")
    else:
        print(f'{prompt}', end=" : ")

    _in = getch()
    if _in == "\n":
        printf(f"\r{prompt} : {default}")
        return default
    else:

        printf(f"\r{prompt}", end=" : ")
        while not (char := getch()) == "\n":
            printf(char, end="")
            _in += char

    return _in


def suggest(suggestion: str) -> Callable:
    row_1, col_1 = get_cursor_pos()
    sys.stdout.write(suggestion)
    row_2, col_2 = get_cursor_pos()
    if i := row_2 - row_1:
        move_cursor_up(steps=i)
    if i := col_2 - col_1:
        move_cursor_left(steps=i)


def common_start(*strings):
    """
    Returns the longest common substring
    from the beginning of the `strings`
    """

    def _iter():
        for z in zip(*strings):
            if z.count(z[0]) == len(z):  # check all elements in `z` are the same
                yield z[0]
            else:
                return

    return ''.join(_iter())


def prompt(msg: str, options: dict):
    sys.stdout.write(msg)
    s = _prompt(options, getch())
    return s.strip()


def _prompt(options: dict, _in: str) -> str:
    if _in.endswith("\n"):
        return _in

    last_word = _in[_in.find(" ") + 1:]

    available_commands = [command for command in options
                          if not (command.startswith("_") and options[command].get("_value"))]
    possible_suggestions = [option for option in available_commands if option.startswith(last_word)]
    suggestion = common_start(*possible_suggestions)

    suggest(suggestion)
    char = getch(decode=False)
    delete_printed(len(suggestion))

    if char in MODIFIER_KEYS.values():
        key = MODIFIER_KEYS(char)

        if key == MODIFIER_KEYS.TAB:
            if suggestion:
                _in += suggestion
                sys.stdout.write(suggestion)
                sys.stdout.flush()
            else:
                print("help")
        elif key == MODIFIER_KEYS.ENTER:
            _in += char
        elif key == MODIFIER_KEYS.BACKSPACE and len(_in):
            _in = _in[:-2]
            delete_printed(1)
    else:
        _in += char.decode()

    s = _prompt(options, _in)

    return ""
