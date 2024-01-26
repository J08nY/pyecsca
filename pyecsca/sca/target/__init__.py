"""Package for communicating with targets of measurement."""

from .ISO7816 import *
from .base import *
from .serial import *
from .simpleserial import *
from .binary import *
from .flash import *
from .leakage import *

has_chipwhisperer: bool = False
has_pyscard: bool = False
has_leia: bool = False

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

try:
    import smartleia

    has_leia = True
except ImportError:  # pragma: no cover
    pass

from .ectester import ECTesterTarget  # noqa

if has_pyscard:
    from .PCSC import *

if has_leia:
    from .leia import *

if has_chipwhisperer:
    from .chipwhisperer import *
