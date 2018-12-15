from typing import List, Tuple

from .formula import Formula
from .mod import Mod
from .point import Point


class Context(object):
    intermediates: List[Tuple[str, Mod]]
    actions: List[Tuple[Formula, Tuple[Point, ...]]]

    def __init__(self):
        self.intermediates = []
        self.actions = []

    def execute(self, formula: Formula, *points: Point, **params: Mod) -> Tuple[Point, ...]:
        if len(points) != formula.num_inputs:
            raise ValueError
        self.actions.append((formula, tuple(points)))
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
        result = []
        for i in range(formula.num_outputs):
            ind = str(i + 3)
            resulting = {variable: locals[variable + ind]
                         for variable in formula.coordinate_model.variables
                         if variable + ind in locals}
            result.append(Point(formula.coordinate_model, **resulting))
        return tuple(result)
