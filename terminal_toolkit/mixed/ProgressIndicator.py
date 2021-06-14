import asyncio


class Wheel:
    """this class produces a small progress wheel.
    usage: make an instance of this object.
    every time __str__ is called on this object the next symbol is returned """

    def __init__(self, interval=0.1):
        self.num = 0
        self.interval = interval
        self.__symbols__ = {
            0: "[|]",
            1: "[/]",
            2: "[-]",
            3: "[\\]"
        }

    async def get_next(self):
        while True:
            self.num += 1
            yield self.__symbols__[self.num % 4]
            await asyncio.sleep(self.interval)


WHEEL = Wheel().get_next()
