libtomcrypt
===========

| Version: ``v1.18.2``
| Repository: https://github.com/libtom/libtomcrypt/
| Docs:

Primitives
----------

Offers ECDH and ECDSA on the `curves <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ecc.c>`__: SECP112r1, SECP128r1, SECP160r1, P-192, P-224, P-256, P-384, P-521.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Simple ladder <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ltc_ecc_mulmod_timing.c#L35>`__ via ``ecc_make_key -> ecc_make_key_ex -> ecc_ptmul -> ltc_ecc_mulmod_timing``.
 - jacobian, `dbl-1998-hnm <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ltc_ecc_projective_dbl_point.c#L32>`__ via ltc_ecc_projective_dbl_point
 - jacobian, `add-1998-hnm <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ltc_ecc_projective_add_point.c#L33>`__ via ltc_ecc_projective_add_point

Derive:
 - Same as Keygen via ``ecc_shared_secret -> ecc_ptmul -> ltc_ecc_mulmod_timing``.

ECDSA
^^^^^

Keygen:
 - Same as ECDH.

Sign:
 - Same as Keygen via ``ecc_sign_hash -> _ecc_sign_hash -> ecc_make_key_ex``.

Verify:
 - `Shamir's trick <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ltc_ecc_mul2add.c#L35>`__ via ``ecc_verify_hash -> _ecc_verify_hash -> ecc_mul2add`` or two separate sliding windows.
 - Same coords and formulas as KeyGen.
