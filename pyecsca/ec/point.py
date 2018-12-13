from typing import Mapping

from .coordinates import CoordinateModel
from .mod import Mod


class Point(object):
    coordinate_model: CoordinateModel
    coords: Mapping[str, Mod]

    def __init__(self, model: CoordinateModel, **coords: Mod):
        if not set(model.variables) == set(coords.keys()):
            raise ValueError
        self.coordinate_model = model
        self.coords = coords

    def __eq__(self, other):
        if type(other) is not Point:
            return False
        return self.coordinate_model == other.coordinate_model and self.coords == other.coords

    def __repr__(self):
        args = ", ".join(["{}={}".format(key, value) for key, value in self.coords.items()])
        return "Point([{}] in {})".format(args, self.coordinate_model)
