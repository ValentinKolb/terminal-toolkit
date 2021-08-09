import math
import time

import terminal_toolkit.console.Console as console


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
    width, _ = console.get_size()
    _, cursor_col = console.get_cursor_pos()

    console.move_cursor_left(min(cursor_col-1, num_chars))
    console.erase_end_of_line()
    num_chars -= cursor_col

    while num_chars > 0:
        console.set_title(f'{width=} {cursor_col=} {num_chars=}')
        console.getch()

        console.move_cursor_up()
        if width > num_chars:
            console.move_cursor_right(width - num_chars - 1)
        num_chars -= width
        console.erase_end_of_line()
    console.set_title(f'{width=} {cursor_col=} {num_chars=}')


def read(prompt: str, default: str = None, hide_input: bool = False, allowed_options: list = None):
    prompt = prompt.rstrip().removesuffix(":")

    if default:
        printf(f'{prompt} [{default}]', end=" : ")
    else:
        print(f'{prompt}', end=" : ")

    _in = console.getch()
    if _in == "\n":
        printf(f"\r{prompt} : {default}")
        return default
    else:

        printf(f"\r{prompt}", end=" : ")
        while not (char := console.getch()) == "\n":
            printf(char, end="")
            _in += char

    return _in


def show_options():
    pass
