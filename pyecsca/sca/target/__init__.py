"""Package for communicating with targets of measurement."""

from .ISO7816 import *
from .base import *
from .serial import *
from .simpleserial import *
from .binary import *
from .flash import *

has_chipwhisperer = False
has_pyscard = False

try:
    import chipwhisperer

    has_chipwhisperer = True
except ImportError:  # pragma: no cover
    pass

try:
    import smartcard

    has_pyscard = True
except ImportError:  # pragma: no cover
    pass

if has_pyscard:
    from .PCSC import *
    from .ectester import ECTesterTarget

if has_chipwhisperer:
    from .chipwhisperer import *
