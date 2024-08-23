NSS
===

| Version: ``3.94``
| Repository: https://hg.mozilla.org/projects/nss
| Docs:


Primitives
----------

ECDH, ECDSA (only standard curves P-256, P-384, P-521), also x25519.

Two ECMethods:
 - Curve25519
    - 32-bit -> own impl
    - 64-bit -> HACL*
 - P-256 from HACL*

Several ECGroups:
 - generic ``ECGroup_consGFp``
 - Montgomery arithmetic ``ECGroup_consGFp_mont``
 - P-256
 - P-384 from ECCkiila
 - P-521 from ECCkiila

The ECMethods override the scalarmult of the ECGroups in:
 - ``ec_NewKey`` via ``ec_get_method_from_name`` and then calling the ``method.mul``.
 - ``EC_ValidatePublicKey`` via ``ec_get_method_from_name`` and then calling the ``method.validate``.
 - ``ECDH_Derive`` via ``ec_get_method_from_name`` and then calling the ``method.mul``.
 - ``ECDSA_SignDigest`` and ``ECDSA_SignDigestWithSeed`` via ``ec_SignDigestWithSeed``, then ``ec_get_method_from_name`` and then calling the ``method.mul``.


P-256 from HACL*
^^^^^^^^^^^^^^^^

KeyGen:
 - Short-Weierstrass
 - Fixed Window (width = 4)? points to https://eprint.iacr.org/2013/816.pdf? via ``ec_secp256r1_pt_mul -> (Hacl*) Hacl_P256_dh_initiator -> point_mul_g``
 - projective-3 coords.
 - `add-2015-rcb`, `dbl-2015-rcb-3`

Derive:
 - Same as KeyGen.

Sign:
 - Same as Keygen.

Verify:
 - Short-Weierstrass
 - Multi-scalar simultaneous Fixed Window
 - Same coords and formulas as KeyGen.

P-384
^^^^^

KeyGen:
 - Short-Weierstrass
 - Comb from ecckiila: ``EC_NewKeyFromSeed -> ec_NewKey -> ec_points_mul -> ECPoints_mul -> ecgroup.points_mul -> point_mul_two_secp384r1_wrap -> point_mul_g_secp384r1_wrap -> point_mul_g_secp384r1 -> fixed_smul_cmb``.
 - projective-3 coords.
 - `dbl-2015-rcb-3`, `madd-2015-rcb-3` also `add-2015-rcb` in point_add_proj.

Derive:
 - Short-Weierstrass
 - Regular Window NAF (width = 5) from ecckiila: ``ECDH_Derive -> ec_points_mul -> ECPoints_mul -> ecgroup.points_mul -> point_mul_secp384r1_wrap -> point_mul_secp384r1 -> var_smul_rwnaf``.
 - projective-3 coords.
 - `dbl-2015-rcb-3`, `add-2015-rcb`.

Sign:
 - Same as KeyGen.

Verify:
 - Short-Weierstrass
 - Interleaved multi-scalar window NAF (width = 5) with Shamir's trick from ecckiila: ``ECDSA_SignDigest -> ECDSA_SignDigestWithSeed -> ec_SignDigestWithSeed -> ec_points_mul -> ECPoints_mul -> ecgroup.points_mul -> point_mul_two_secp384r1_wrap -> point_mul_two_secp384r1 -> var_smul_wnaf_two``
 - projective-3 coords.
 - `dbl-2015-rcb-3`, `madd-2015-rcb-3` also `add-2015-rcb` in point_add_proj.

P-521
^^^^^

Same as P-384.

x25519
^^^^^^

KeyGen:
 - Montgomery
 - Montgomery ladder via ``-> ec_Curve25519_pt_mul -> ec_Curve25519_mul``.
 - xz coords
 - Unknown formulas: `ladd-hacl-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-hacl-x25519.op3>`__,
   `dbl-hacl-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-hacl-x25519.op3>`__

Derive:
 - Same as KeyGen.
