"""Package for handling oscilloscopes for measurement of power/EM traces."""

from typing import Type

from .base import *

has_picoscope = False
has_picosdk = False
has_chipwhisperer = False

try:
    import picoscope

    has_picoscope = True
except ImportError:  # pragma: no cover
    pass

try:
    import picosdk

    has_picosdk = True
except ImportError:  # pragma: no cover
    pass

try:
    import chipwhisperer

    has_chipwhisperer = True
except ImportError:  # pragma: no cover
    pass

PicoScope: Type[Scope]
if has_picoscope:
    from .picoscope_alt import *

    PicoScope = PicoScopeAlt
elif has_picosdk:
    from .picoscope_sdk import *

    PicoScope = PicoScopeSdk

if has_chipwhisperer:
    from .chipwhisperer import *
