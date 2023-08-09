import pytest

from pyecsca.ec.params import get_params, DomainParameters


@pytest.fixture(scope="session")
def secp128r1() -> DomainParameters:
    return get_params("secg", "secp128r1", "projective")


@pytest.fixture(scope="session")
def curve25519() -> DomainParameters:
    return get_params("other", "Curve25519", "xz")


@pytest.fixture(scope="session")
def ed25519() -> DomainParameters:
    return get_params("other", "Ed25519", "projective")
