import asyncio
import time

import terminal_toolkit.console.Utils as utils
import terminal_toolkit.console.Console as console


def testn(n: int):
    s = "#" * n

    print("ANFANG:", end="", flush=True)
    print(s, end="", flush=True)
    utils.delete_printed(n)
    print("ENDE")



def test1():
    testn(1000)


if __name__ == '__main__':
    # result = read("Test", default="default", allowed_options=["1", "2", "3"], hide_input=False)
    # print(f'{result=}')
    for i in (10,100, 1000):
        testn(i)
