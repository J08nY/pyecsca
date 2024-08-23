SymCrypt
========

| Version: ``103.1.0`` (tag v103.1.0)
| Repository: https://github.com/microsoft/SymCrypt
| Docs:

Primitives
----------

Supports ECDH and ECDSA with `NIST <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_internal_curves.c#L16C19-L16C25>`__ curves (192, 224, 256, 384, 521) and Twisted Edwards `NUMS <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_internal_curves.c#L303>`__ curves (NumsP256t1, NumsP384t1, NumsP512t1).
Also custom curves.
Supports X25519.


ECDH
^^^^

KeyGen:
 - `(signed) Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcpointGenericSetRandom -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__.
 - NIST (Short-Weierstrass) use `Jacobian <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ecurve.c#L101>`__.
    - `dbl-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L381>`__ for generic double via ``SymCryptEcpointDouble`` or a `tweak of  dbl-2007-bl/dbl-2001-b <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L499>`__ formulae via ``SymCryptShortWeierstrassDoubleSpecializedAm3`` for ``a=-3``.
    - `add-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L490>`__ via ``SymCryptEcpointAddDiffNonZero``. It also has side-channel unsafe version ``SymCryptShortWeierstrassAddSideChannelUnsafe`` and a generic wrapper for both via ``SymCryptEcpointAdd``.
 - NUMS (Twisted-Edwards) curves use `Extended projective <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ecurve.c#L104>`__.
    - `dbl-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_twisted_edwards.c#L195>`__ via ``SymCryptTwistedEdwardsDouble``.
    - `add-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_twisted_edwards.c#L313>`__ via ``SymCryptTwistedEdwardsAdd`` or ``SymCryptTwistedEdwardsAddDiffNonZero``.

Derive:
 - `(signed) Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDhSecretAgreement -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__.
 - Same coordinates and formulas as KeyGen.


ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `(signed) Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcpointGenericSetRandom -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__.
 - NIST (Short-Weierstrass) use `Jacobian <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ecurve.c#L101>`__.
    - `dbl-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L381>`__ for generic double via ``SymCryptEcpointDouble`` or a `tweak of  dbl-2007-bl/dbl-2001-b <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L499>`__ formulae via ``SymCryptShortWeierstrassDoubleSpecializedAm3`` for ``a=-3``.
    - `add-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L490>`__ via ``SymCryptEcpointAddDiffNonZero``. It also has side-channel unsafe version ``SymCryptShortWeierstrassAddSideChannelUnsafe`` and a generic wrapper for both via ``SymCryptEcpointAdd``.
 - NUMS (Twisted-Edwards) curves use `Extended projective <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ecurve.c#L104>`__.
    - `dbl-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_twisted_edwards.c#L195>`__ via ``SymCryptTwistedEdwardsDouble``.
    - `add-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_twisted_edwards.c#L313>`__ via ``SymCryptTwistedEdwardsAdd`` or ``SymCryptTwistedEdwardsAddDiffNonZero``.


Sign:
 - Short-Weierstrass
 - `(signed) Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDsaSignEx -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__.
 - Same coordinates and formulas as KeyGen.

Verify:
 - Short-Weierstrass
 - `Double-scalar multiplication using the width-w NAF with interleaving <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDsaVerify > SymCryptEcpointMultiScalarMul -> SymCryptEcpointMultiScalarMulWnafWithInterleaving``. Algorithm 9 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__.
 - Same coordinates and formulas as KeyGen.

X25519
^^^^^^

KeyGen:
 - Montgomery
 - `Ladder <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_montgomery.c#L297>`__ via
   ``SymCryptMontgomeryPointScalarMul``.
 - `xz <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_montgomery.c#L173>`__.
 - `ladd-1987-m-3 <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_montgomery.c#L151>`__  via ``SymCryptMontgomeryDoubleAndAdd``.


Derive:
 - Same as Keygen.
