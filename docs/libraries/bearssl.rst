BearSSL
=======

| Version: ``v0.6``
| Repository: https://bearssl.org/gitweb/?p=BearSSL;a=summary
| Docs: https://bearssl.org/index.html

Primitives
----------

Supports SECG prime field curves, as well as Brainpool and Curve25519, Curve448.
Has API functions for ECDSA, but does ECDH only implicitly in its TLS implementation (no public API exposed).
Unclear whether Ed25519 is supported.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - (width=2) Fixed Window via ``br_ec_compute_pub -> impl.mulgen -> impl.mul``, but (width=4) Fixed Window via ``br_ec_compute_pub -> impl.mulgen`` for special (P-256) curves.
 - Jacobian coordinates
 - Unknown formulas: `add-bearssl-v06 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-bearssl-v06.op3>`__,
   `dbl-bearssl-v06 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-bearssl-v06.op3>`__,

Derive:
 - Short-Weierstrass
 - (width=2) Fixed Window via ``impl.mul``.
 - Coordinates and formulas same as in KeyGen.

ECDSA
^^^^^

KeyGen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - (width=2) Fixed Window via ``br_ecdsa_*_sign_raw -> impl.mulgen -> impl.mul``, but (width=4) Fixed Window via ``br_ecdsa_*_sign_raw -> impl.mulgen`` for special (P-256) curves.
 - Coordinates and formulas same as in KeyGen.

Verify:
 - Short-Weierstrass
 - Simple scalarmult then add via ``br_ecdsa_*_verify_raw -> impl.muladd -> impl.mul + add``
 - Coordinates and formulas same as in KeyGen.

x25519
^^^^^^

KeyGen:
 - Montgomery
 - Montgomery ladder via ``br_ec_compute_pub -> impl.mulgen -> impl.mul``.
 - xz coordinates
 - ladd-rfc7748

Derive:
 - Same as KeyGen.
