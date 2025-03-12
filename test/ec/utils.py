from functools import reduce
from itertools import product


def cartesian(*items):
    for cart in product(*items):
        yield reduce(lambda x, y: x + y, cart)
