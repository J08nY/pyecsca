from typing import List, Tuple

from .formula import Formula
from .mod import Mod
from .point import Point


class Context(object):
    intermediates: List[Tuple[str, Mod]]

    def __init__(self):
        self.intermediates = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, formula: Formula, *points: Point, **params: Mod) -> Point:
        coords = {}
        for i, point in enumerate(points):
            if point.coordinate_model != formula.coordinate_model:
                raise ValueError
            for coord, value in point.coords.items():
                coords[coord + str(i + 1)] = value
        locals = {**coords, **params}
        previous_locals = set(locals.keys())
        for line in formula.code:
            exec(compile(line, "", mode="exec"), {}, locals)
            diff = set(locals.keys()).difference(previous_locals)
            previous_locals = set(locals.keys())
            for key in diff:
                self.intermediates.append((key, locals[key]))
        resulting = {variable: locals[variable + "3"]
                     for variable in formula.coordinate_model.variables
                     if variable + "3" in locals}
        return Point(formula.coordinate_model, **resulting)
