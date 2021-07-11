from dataclasses import dataclass, field
from typing import Literal, Union, Optional


@dataclass
class WidgetSize:
    mode: Literal["absolute", "relative"] = "absolute"
    width: Union[float, str] = 1.0
    height: Union[float, str] = 1.0

    def get_size(self, abs_size: tuple[int, int], rel_size: tuple[int, int]) -> tuple[int, int]:
        """
        returns the width and height

        Parameters
        ----------
        abs_size
        rel_size

        Returns
        -------

        """
        x, y = rel_size if self.mode == "relative" else abs_size

        if isinstance(self.width, str):
            width = int(self.width.replace("px", "").strip())
        else:
            width = int(self.width * x)

        if isinstance(self.height, str):
            height = int(self.height.replace("px", "").strip())
        else:
            height = int(self.height * y)

        return width, height


@dataclass
class WidgetStyle:
    size: WidgetSize = field(default_factory=WidgetSize)
    color: Optional = None
    background_color = None
