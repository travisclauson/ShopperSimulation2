from enum import Enum


class CartState(Enum):
    NONE = 0,
    EMPTY = 1,
    FULL = 2,
    PURCHASED = 3
