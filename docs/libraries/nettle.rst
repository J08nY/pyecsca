Nettle
======

| Version: ``3.9.1``
| Repository: https://git.lysator.liu.se/nettle/nettle
| Docs: https://www.lysator.liu.se/~nisse/nettle/nettle.html

Primitives
----------

ECDSA on P192, P224, P256, P384 and P521, also EdDSA on Curve25519, Curve448.

.. csv-table:: Pippenger parameters
    :header: "Curve", "K", "C"

    P192, 8, 6
    P224, 16, 7
    P256, 11, 6
    P384, 32, 6
    P521, 44, 6
    Curve25519, 11, 6

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g.c?ref_type=tags#L44>`__ via ``ecdsa_generate_keypair -> ecc_curve.mul_g -> ecc_mul_g``.
 - Jacobian
 - `madd-2007-bl <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-add-jja.c?ref_type=tags#L53>`__, `dbl-2001-b <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-dup-jj.c?ref_type=tags#L46>`__

Sign:
 - Short-Weierstrass
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g.c?ref_type=tags#L44>`__ via ``ecc_ecdsa_sign -> ecc_mul_g``.
 - Same as KeyGen.


Verify:
 - Short-Weierstrass
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g.c?ref_type=tags#L44>`__ and `4-bit Fixed Window <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-a.c?ref_type=tags#L52>`__ via ``ecc_ecdsa_verify -> ecc_mul_a + ecc_mul_g``.
 - Jacobian
 - `madd-2007-bl <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-add-jja.c?ref_type=tags#L53>`__, `dbl-2001-b <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-dup-jj.c?ref_type=tags#L46>`__,
   also `add-2007-bl <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-add-jjj.c?ref_type=tags#L42>`__.

Ed25519
^^^^^^^

KeyGen:
 - Twisted Edwards
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g-eh.c?ref_type=tags#L44>`__ via ``ed25519_sha512_public_key -> _eddsa_public_key -> ecc_curve.mul_g -> ecc_mul_g_eh``.
 - Projective
 - `madd-2008-bbjlp <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-add-th.c?ref_type=tags#L42>`__, `add-2008-bbjlp <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-add-thh.c?ref_type=tags#L41>`__ and `dup-2008-bbjlp <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-dup-th.c?ref_type=tags#L41>`__.

Sign:
 - Twisted Edwards
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g-eh.c?ref_type=tags#L44>`__ via ``ed25519_sha512_sign -> _eddsa_sign -> ecc_curve.mul_g -> ecc_mul_g_eh``.
 - Same as KeyGen.

Verify:
 - Twisted Edwards
 - `Pippenger <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-g-eh.c?ref_type=tags#L44>`__ and `4-bit Fixed Window <https://git.lysator.liu.se/nettle/nettle/-/blob/nettle_3.9.1_release_20230601/ecc-mul-a-eh.c?ref_type=tags#L116>`__ via ``ed25519_sha512_verify -> _eddsa_verify -> ecc_curve.mul + ecc_curve.mul_g``.
 - Same as KeyGen.
