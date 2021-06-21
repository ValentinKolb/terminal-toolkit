import os
import sys
import termios
from typing import TextIO

from terminal_toolkit.console import Console

if __name__ == '__main__':
    while (c := Console.getch(blocking=True)) != 'q':
        print(c)
