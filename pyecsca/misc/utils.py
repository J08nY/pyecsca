"""Just some utilities I promise."""
from ast import parse


def pexec(s):
    return parse(s, mode="exec")


def peval(s):
    return parse(s, mode="eval")
