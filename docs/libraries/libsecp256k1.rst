libsecp256k1
============

| Version: ``v0.4.0``
| Repository: https://github.com/bitcoin-core/secp256k1
| Docs:

Primitives
----------

Supports ECDSA, ECDH and Schnorr signatures over secp256k1.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Fixed window with full precomputation <https://github.com/bitcoin-core/secp256k1/blob/v0.4.0/src/ecmult_gen_impl.h#L45>`__ via ``secp256k1_ec_pubkey_create -> secp256k1_ec_pubkey_create_helper -> secp256k1_ecmult_gen``. Window of size 4.
 - Uses scalar blinding.
 - `Jacobian version of add-2002-bj <https://github.com/bitcoin-core/secp256k1/blob/v0.4.0/src/group_impl.h#L670>`__  (via ``secp256k1_gej_add_ge``).
 - No doubling.


Derive:
 - Uses GLV decomposition and `interleaving with width-5 NAFs <https://github.com/bitcoin-core/secp256k1/blob/v0.4.0/src/ecmult_const_impl.h#L133>`__ via ``secp256k1_ecdh -> secp256k1_ecmult_const``.
 - Addition same as in Keygen.
 - Unknown doubling: `dbl-secp256k1-v040 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-secp256k1-v040>`__ (via `secp256k1_gej_double <https://github.com/bitcoin-core/secp256k1/blob/v0.4.0/src/group_impl.h#L406>`__)

ECDSA
^^^^^

Keygen:
 - Same as ECDH.

Sign:
 - Same as Keygen via ``secp256k1_ecdsa_sign -> secp256k1_ecdsa_sign_inner -> secp256k1_ecdsa_sig_sign -> secp256k1_ecmult_gen``.

Verify:
 - Split both scalars using GLV and then interleaving with width-5 NAFS on 4 scalars via ``secp256k1_ecdsa_verify -> secp256k1_ecdsa_sig_verify -> secp256k1_ecmult -> secp256k1_ecmult_strauss_wnaf``.
 - DBL same as in ECDH DERIVE. Two formulas for addition are implemented. For the generator part, same addition as in Keygen is used. For public key, the following::

    assume iZ2 = 1/Z2
    az = Z_1*iZ2
    Z12 = az^2
    u1 = X1
    u2 = X2*Z12
    s1 = Y1
    s2 = Y2*Z12
    s2 = s2*az
    h = -u1
    h = h+u2
    i = -s2
    i = i+s1
    Z3 = Z1*h
    h2 = h^2
    h2 = -h2
    h3 = h2*h
    t = u1*h2
    X3 = i^2
    X3 = X3+h3
    X3 = X3+t
    X3 = X3+t
    t = t+X3
    Y3 = t*i
    h3 = h3*s1
    Y3 = Y3+h3

 - Before the addition the Jacobian coordinates are mapped to an isomorphic curve.
