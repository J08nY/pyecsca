import cython


@cython.cclass
class Test:
    def __new__(cls, *args, **kwargs):
        pass
