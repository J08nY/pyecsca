BoringSSL
=========

| Version: ``bfa8369`` (commit bfa8369)
| Repository: https://github.com/google/boringssl/
| Docs: https://commondatastorage.googleapis.com/chromium-boringssl-docs/headers.html

Primitives
----------

Supports P-224, P-256, P-384 and P-521.
Also Curve25519.
Uses fiat-crypto for the SECP curve field arithmetic and x25519.

P-224
^^^^^
 - Short-Weierstrass
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L995>`__ via ``mul_base -> ec_GFp_nistp224_point_mul_base``.
   `Fixed Window (signed, Booth) (width=5) <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L947C13-L947C38>`__ via ``mul -> ec_GFp_nistp224_point_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L580>`__,
 - Formulas unknown: `add-boringssl-p224 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-boringssl-p224.op3>`__,
   `dbl-boringssl-p224 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-boringssl-p224.op3>`__.

P-256
^^^^^
 - Short-Weierstrass
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L543>`__ via ``mul_base -> ec_GFp_nistp256_point_mul_base``.
   `Fixed Window (signed, Booth) (width=5) <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L476>`__ via ``mul -> ec_GFp_nistp256_point_mul``.
 - `Jacobian-3 <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L238>`__,
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L238>`__,
   `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L184>`__

P-384
^^^^^
 - Uses defaults (described below).

P-521
^^^^^
 - Uses defaults (described below).

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - ``EC_KEY_generate_key -> ec_point_mul_scalar_base -> meth.mul_base``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`__, via ``ec_GFp_mont_mul_base -> ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`__

Derive:
 - Short-Weierstrass
 - ``ECDH_compute_key -> ec_point_mul_scalar -> meth.mul``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`__, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`__

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - ``EC_KEY_generate_key -> ec_point_mul_scalar_base -> meth.mul_base``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`__, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`__

Sign:
 - Short-Weierstrass
 - ``ECDSA_sign -> ECDSA_do_sign -> ecdsa_sign_impl -> ec_point_mul_scalar_base -> meth.mul_base``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`__, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`__

Verify:
 - Short-Weierstrass
 - ``ECDSA_verify -> ECDSA_do_verify -> ecdsa_do_verify_no_self_test -> ec_point_mul_scalar_public -> meth.mul_public or meth.mul_public_batch``.
   Default: `Window NAF (w=4) based interleaving multi-exponentiation method <https://github.com/google/boringssl/blob/bfa8369/crypto/fipsmodule/ec/wnaf.c#L83>`__, via ``ec_GFp_mont_mul_public_batch``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`__, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`__

X25519
^^^^^^

KeyGen:
 - Twisted-Edwards
 - ?? via ``X25519_keypair -> X25519_public_from_private -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`__: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`__, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`__

Derive:
 - Montgomery
 - Ladder via ``X25519 -> x25519_scalar_mult -> x25519_NEON/x25519_scalar_mult_adx/x25519_scalar_mult_generic``
 - xz.
 - Unknown formula: `ladd-boringssl-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-boringssl-x25519.op3>`__ from fiat-crypto.

Ed25519
^^^^^^^
Based on ref10 of Ed25519.

KeyGen:
 - Twisted-Edwards
 - ?? via ``ED25519_keypair -> ED25519_keypair_from_seed -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`__: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`__, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`__

Sign:
 - Twisted-Edwards
 - ?? via ``ED25519_sign -> ED25519_keypair_from_seed -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`__: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`__, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`__

Verify:
 - Twisted-Edwards
 - Sliding window (signed) with interleaving? via ``ED25519_verify -> ge_double_scalarmult_vartime``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`__: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`__, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`__
