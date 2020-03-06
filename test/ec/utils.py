from itertools import product
from functools import reduce

def slow(func):
    func.slow = 1
    return func

def cartesian(*items):
    for cart in product(*items):
        yield reduce(lambda x, y: x + y, cart)