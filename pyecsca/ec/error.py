from public import public


@public
class NonInvertibleError(ArithmeticError):
    pass


@public
class NonInvertibleWarning(UserWarning):
    pass


@public
class NonResidueError(ArithmeticError):
    pass


@public
class NonResidueWarning(UserWarning):
    pass


@public
class UnsatisfiedAssumptionError(ValueError):
    pass


@public
class UnsatisfiedAssumptionWarning(UserWarning):
    pass
