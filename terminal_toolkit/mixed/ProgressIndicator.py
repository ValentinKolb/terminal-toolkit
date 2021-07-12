class Wheel:
    """this class produces a small progress wheel.
    usage: make an instance of this object.
    every time __str__ is called on this object the next symbol is returned """

    def __init__(self):
        self.num = 0
        self.__symbols__ = {
            0: "[|]",
            1: "[/]",
            2: "[-]",
            3: "[\\]"
        }

    def __str__(self) -> str:
        self.num += 1
        return self.__symbols__[self.num % 4]
