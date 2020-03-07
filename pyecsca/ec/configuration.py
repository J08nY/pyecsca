from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import get_type_hints, Union, get_origin, get_args, Generator, FrozenSet

from public import public

from .coordinates import CoordinateModel
from .formula import Formula
from .model import CurveModel
from .mult import ScalarMultiplier


@public
class EnumDefine(Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    @classmethod
    def names(cls):
        return list(e.name for e in cls)

    @classmethod
    def values(cls):
        return list(e.value for e in cls)


@public
class Multiplication(EnumDefine):
    """Base multiplication algorithm to use."""
    TOOM_COOK = "MUL_TOOM_COOK"
    KARATSUBA = "MUL_KARATSUBA"
    COMBA = "MUL_COMBA"
    BASE = "MUL_BASE"


@public
class Squaring(EnumDefine):
    """Base squaring algorithm to use."""
    TOOM_COOK = "SQR_TOOM_COOK"
    KARATSUBA = "SQR_KARATSUBA"
    COMBA = "SQR_COMBA"
    BASE = "SQR_BASE"


@public
class Reduction(EnumDefine):
    """Modular reduction method used."""
    BARRETT = "RED_BARRETT"
    MONTGOMERY = "RED_MONTGOMERY"
    BASE = "RED_BASE"


@public
class Inversion(EnumDefine):
    """Inversion algorithm used."""
    GCD = "INV_GCD"
    EULER = "INV_EULER"


@public
class HashType(EnumDefine):
    """Hash algorithm used in ECDH and ECDSA."""
    NONE = "HASH_NONE"
    SHA1 = "HASH_SHA1"
    SHA224 = "HASH_SHA224"
    SHA256 = "HASH_SHA256"
    SHA384 = "HASH_SHA384"
    SHA512 = "HASH_SHA512"


@public
class RandomMod(EnumDefine):
    """Method of sampling a uniform integer modulo order."""
    SAMPLE = "MOD_RAND_SAMPLE"
    REDUCE = "MOD_RAND_REDUCE"


@public
@dataclass(frozen=True)
class Configuration(object):
    """An ECC implementation configuration."""
    model: CurveModel
    coords: CoordinateModel
    formulas: FrozenSet[Formula]
    scalarmult: ScalarMultiplier
    hash_type: HashType
    mod_rand: RandomMod
    mult: Multiplication
    sqr: Squaring
    red: Reduction
    inv: Inversion


@public
def all_configurations(**kwargs) -> Generator[Configuration, Configuration, None]:
    """
    Get all implementation configurations that match the given `kwargs`.
    The keys in `kwargs` should be some of the attributes in the :py:class:`Configuration`,
    and the values limit the returned configurations to configuration matching them.

    .. note::
        The `formulas` attribute is unsupported and formulas should be provided using the `scalarmult`
        attribute, which is either a subclass of the :py:class:`ScalarMultiplier` class or an instance
        of it or a dictionary giving arguments to a constructor of some :py:class:`ScalarMultiplier`
        subclass.

    .. warning::
        The returned number of configurations might be quite large and take up significant
        memory space.

    :param kwargs: The configuration parameters to match.
    :return: A generator of the configurations
    """

    def is_optional(arg_type):
        return get_origin(arg_type) == Union and len(get_args(arg_type)) == 2 and \
               get_args(arg_type)[1] == type(None)  # noqa

    def leaf_subclasses(cls):
        subs = cls.__subclasses__()
        result = []
        for subclass in subs:
            if subclass.__subclasses__():
                result.extend(leaf_subclasses(subclass))
            else:
                result.append(subclass)
        return result

    def independents(kwargs):
        options = {
            "hash_type": HashType,
            "mod_rand": RandomMod,
            "mult": Multiplication,
            "sqr": Squaring,
            "red": Reduction,
            "inv": Inversion
        }
        keys = list(filter(lambda key: key not in kwargs, options.keys()))
        values = [options[key] for key in keys]
        fixed_args = {key: kwargs[key] for key in kwargs if key in options}
        for value_choice in product(*values):
            yield dict(zip(keys, value_choice), **fixed_args)

    def multipliers(mult_classes, coords_formulas, fixed_args=None):
        for mult_cls in mult_classes:
            if fixed_args is not None and "cls" in fixed_args and mult_cls != fixed_args["cls"]:
                continue
            arg_options = {}
            for name, required_type in get_type_hints(mult_cls.__init__).items():
                if fixed_args is not None and name in fixed_args:
                    arg_options[name] = [fixed_args[name]]
                    continue
                if is_optional(required_type):
                    opt_type = get_args(required_type)[0]
                    if issubclass(opt_type, Formula):
                        options = [formula for formula in coords_formulas if
                                   isinstance(formula, opt_type)] + [None]
                    else:
                        options = [None]  # TODO: anything here?
                elif get_origin(required_type) is None and issubclass(required_type, Formula):
                    options = [formula for formula in coords_formulas if
                               isinstance(formula, required_type)]
                elif get_origin(required_type) is None and issubclass(required_type, bool):
                    options = [True, False]
                elif get_origin(required_type) is None and issubclass(required_type,
                                                                      int) and name == "width":
                    options = [3, 5]
                else:
                    options = []
                arg_options[name] = options
            keys = arg_options.keys()
            values = arg_options.values()
            for combination in product(*values):
                try:
                    mult = mult_cls(**dict(zip(keys, combination)))
                except Exception:
                    continue
                yield mult

    for model_cls in leaf_subclasses(CurveModel):
        model = model_cls()
        if "model" in kwargs:
            if model != kwargs["model"]:
                continue
        for coords_name, coords in model.coordinates.items():
            if "coords" in kwargs:
                if coords != kwargs["coords"]:
                    continue
            coords_formulas = coords.formulas.values()
            mult_classes = leaf_subclasses(ScalarMultiplier)
            if "scalarmult" in kwargs:
                if isinstance(kwargs["scalarmult"], ScalarMultiplier):
                    mults = [kwargs["scalarmult"]]
                    if not set(kwargs["scalarmult"].formulas.values()).issubset(coords_formulas):
                        continue
                elif isinstance(kwargs["scalarmult"], type) and issubclass(kwargs["scalarmult"],
                                                                           ScalarMultiplier):
                    mult_classes = list(
                            filter(lambda mult: issubclass(mult, kwargs["scalarmult"]),
                                   mult_classes))
                    mults = multipliers(mult_classes, coords_formulas)
                else:
                    mults = multipliers(mult_classes, coords_formulas, kwargs["scalarmult"])
            else:
                mults = multipliers(mult_classes, coords_formulas)
            for mult in mults:
                formulas = frozenset(mult.formulas.values())
                for independent_args in independents(kwargs):
                    yield Configuration(model, coords, formulas, mult, **independent_args)
