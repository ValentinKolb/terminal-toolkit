import asyncio
import time

import json

import pprint

from terminal_toolkit.console.Console import getch
from terminal_toolkit.console.Utils import suggest

if __name__ == '__main__':
    options = {
        "first": {

            "_value": int,
            "_desc": "the first option is an integer",

            "first-option-1": {},
            "first-option-2": {}
        },
        "second": {
            "second-option-2": {},
            "second-option-3": {
                "_value": str,
                "_desc": "some string to enter"
            }
        },
        "third": {

        }
    }

    while True:
        print(f'{getch()!r}')
