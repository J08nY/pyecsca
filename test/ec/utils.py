from itertools import product
from functools import reduce


def cartesian(*items):
    for cart in product(*items):
        yield reduce(lambda x, y: x + y, cart)
