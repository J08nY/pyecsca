def test_scopes():
    # Just imports for now to fix bogus coverage
    try:
        from pyecsca.sca.scope.chipwhisperer import ChipWhispererScope
    except ImportError:
        pass
    try:
        from pyecsca.sca.scope.picoscope_alt import PicoScopeAlt
    except ImportError:
        pass
    try:
        from pyecsca.sca.scope.picoscope_sdk import PicoScopeSdk
    except ImportError:
        pass
