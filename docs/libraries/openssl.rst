OpenSSL
=======

| Version: ``3.1.4``
| Repository: https://github.com/openssl/openssl
| Docs: https://www.openssl.org/docs/

Primitives
----------

ECDH, ECDSA on standard and custom curves.
x25519, x448 and Ed25519, Ed448.
Also SM2 specific methods.

The ladder methods have coordinate randomization and fix scalar bit-length.

Has several EC_METHODs.
 - EC_GFp_simple_method
 - EC_GFp_mont_method
 - EC_GFp_nist_method
 - EC_GFp_nistp224_method
 - EC_GFp_nistp256_method
 - EC_GFp_nistz256_method
 - EC_GFp_nistp521_method

`ossl_ec_GFp_simple_ladder_pre <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_smpl.c#L1493>`__:
 - Short-Weierstrass
 - xz
 - dbl-2002-it-2

`ossl_ec_GFp_simple_ladder_step <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_smpl.c#L1563>`__:
 - Short-Weierstrass
 - xz
 - mladd-2002-it-4

`ossl_ec_GFp_simple_ladder_post <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_smpl.c#L1651>`__:
 - Short-Weierstrass
 - xz to y-recovery

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - ? via ``EVP_EC_gen -> EVP_PKEY_Q_keygen -> evp_pkey_keygen -> EVP_PKEY_generate -> evp_keymgmt_util_gen -> evp_keymgmt_gen -> EC_KEYMGMT.gen -> ec_gen -> EC_KEY_generate_key -> ec_method.keygen  -> ossl_ec_key_simple_generate_key -> EC_POINT_mul(k, G, NULL, NULL)`` all methods then either ec_method.mul or ossl_ec_wNAF_mul
    - EC_GFp_simple_method -> ossl_ec_wNAF_mul -> `ossl_ec_scalar_mul_ladder <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ec_mult.c#L145>`__ (Lopez-Dahab ladder) for [k]G and [k]P. Otherwise multi-scalar wNAF with interleaving?
    - EC_GFp_mont_method -> ossl_ec_wNAF_mul -> `ossl_ec_scalar_mul_ladder <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ec_mult.c#L145>`__ (Lopez-Dahab ladder) for [k]G and [k]P. Otherwise multi-scalar wNAF with interleaving?
    - EC_GFp_nist_method -> ossl_ec_wNAF_mul -> `ossl_ec_scalar_mul_ladder <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ec_mult.c#L145>`__ (Lopez-Dahab ladder) for [k]G and [k]P. Otherwise multi-scalar wNAF with interleaving?
       - ec_point_ladder_pre -> ec_method.ladder_pre or EC_POINT_dbl
       - ec_point_ladder_step -> ec_method.ladder_step or EC_POINT_add + EC_POINT_dbl
       - ec_point_ladder_post -> ec_method.ladder_post
       - the methods all use ossl_ec_GFp_simple_ladder_* functions as ladder_*.
    - EC_GFp_nistp224_method -> ossl_ec_GFp_nistp224_points_mul -> Comb for generator, (signed, Booth) Fixed Window (width = 5) for other points.
    - EC_GFp_nistp256_method -> ossl_ec_GFp_nistp256_points_mul -> Comb for generator, (signed, Booth) Fixed Window (width = 5) for other points.
    - EC_GFp_nistz256_method -> ecp_nistz256_points_mul -> (signed, `Booth <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistputil.c#L141>`__) Fixed Window (width = 7) with full precomputation from [SG14]_.
    - EC_GFp_nistp521_method -> ossl_ec_GFp_nistp521_points_mul -> Comb for generator, (signed, Booth) Fixed Window (width = 5) for other points.
 - Jacobian (or Jacobian-3 for NIST)
 - Formulas:
    - EC_GFp_simple_method -> LibreSSL add and LibreSSL dbl
    - EC_GFp_mont_method -> LibreSSL add and LibreSSL dbl
    - EC_GFp_nist_method -> LibreSSL add and LibreSSL dbl
    - EC_GFp_nistp224_method -> BoringSSL P-224 add and dbl
    - EC_GFp_nistp256_method -> `add-2007-bl <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistp256.c#L1235>`__, `dbl-2001-b <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistp256.c#L1104>`__
    - EC_GFp_nistz256_method -> Unknown: `add-openssl-z256 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-openssl-z256.op3>`__, `add-openssl-z256a <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-openssl-z256a.op3>`__
    - EC_GFp_nistp521_method -> `add-2007-bl <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistp521.c#L1205>`__, `dbl-2001-b <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistp521.c#L1087>`__

Derive:
 - Same as KeyGen, except for:
    - nistp{224,256,521} methods, where the Fixed Window branch of the scalar multiplier is taken,
    - nistz256 where a (signed, `Booth <https://github.com/openssl/openssl/blob/openssl-3.1.4/crypto/ec/ecp_nistputil.c#L141>`__) Fixed Window (width = 5) is taken.

ECDSA
^^^^^

KeyGen:
 - Same as ECDH.

Sign:
 - Same as KeyGen.

Verify:
 - Short-Weierstrass
 - EC_GFp_simple_method, EC_GFp_mont_method, EC_GFp_nist_method: Interleaved multi-scalar wNAF via ``ec_method.verify_sig -> ossl_ecdsa_simple_verify_sig -> EC_POINT_mul -> ossl_ec_wNAF_mul``.
 - EC_GFp_nistp224_method, EC_GFp_nistp256_method, EC_GFp_nistp521_method: Interleaved Comb for G and (signed, Booth) Fixed Window (width = 5) for other point.
 - EC_GFp_nistz256_method: Same as KeyGen for G and same as ECDH Derive for other point.

x25519
^^^^^^
Taken from ref10 of Ed25519. See :doc:`boringssl`.

KeyGen:
 - Twisted-Edwards
 - Pippenger via ``ossl_x25519_public_from_private -> ge_scalarmult_base``.
 - Mixes coordinate models::

     ge_p2 (projective): (X:Y:Z) satisfying x=X/Z, y=Y/Z
     ge_p3 (extended): (X:Y:Z:T) satisfying x=X/Z, y=Y/Z, XY=ZT
     ge_p1p1 (completed): ((X:Z),(Y:T)) satisfying x=X/Z, y=Y/T
     ge_precomp (Duif): (y+x,y-x,2dxy)

Derive:
 - Montgomery
 - Montgomery ladder via ``ossl_x25519 -> x25519_scalar_mult``
 - xz coords
 - Unknown ladder formula: `ladd-openssl-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-openssl-x25519.op3>`__

Ed25519
^^^^^^^
Taken from ref10 of Ed25519. See :doc:`boringssl`.

KeyGen:
 - Same as x25519 KeyGen via ``ossl_ed25519_public_from_private -> ge_scalarmult_base``.

Sign:
 - Same as x25519 KeyGen via ``ossl_ed25519_sign -> ge_scalarmult_base``.

Verify:
 - Sliding window (signed) with interleaving? via ``ossl_ed25519_verify -> ge_double_scalarmult_vartime``.
 - Otherwise same mixed coordinates and formulas.
