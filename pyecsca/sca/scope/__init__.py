try:
    import picosdk
    from .picoscope import *
except ImportError:
    pass

try:
    import chipwhisperer
    from .chipwhisperer import *
except ImportError:
    pass
