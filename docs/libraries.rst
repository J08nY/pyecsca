================
ECC in Libraries
================

BouncyCastle
============

| Version: ``1.76`` (tag r1rv76)
| Repository: https://github.com/bcgit/bc-java/
| Docs: https://bouncycastle.org/docs/docs1.8on/index.html

Primitives
----------

Supports short-Weierstrass curves for the usual (ECDSA, ECDH).
Supports X25519, Ed25519.
Also more exotic stuff like ECMQV, GOST key exchange and signatures
and lots of others.

Lots of `scalarmults <https://github.com/bcgit/bc-java/tree/r1rv76/core/src/main/java/org/bouncycastle/math/ec>`_ available:
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/FixedPointCombMultiplier.java>`_
 - `GLV <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/GLVMultiplier.java>`_
 - `Window NAF L2R <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/WNafL2RMultiplier.java>`_
 - `Window "tau" NAF <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/WTauNafMultiplier.java>`_

Several `coordinate systems <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L27>`_ supported:
 - Affine
 - Projective (Homogenous)
 - Jaobian
 - Jacobian-Chudnovsky
 - Jacobian-Modified
 - Lambda-Affine? (binary-field curves only)
 - Lambda-Projective? (binary-field curves only)
 - Skewed? (binary-field curves only)

Some curve-custom code in:
https://github.com/bcgit/bc-java/tree/r1rv76/core/src/main/java/org/bouncycastle/math/ec/custom/sec
Specifically, fast-prime modular reduction for SECG curves, and (weirdly) a short-Weierstrass implementation of Curve25519.

Ed25519 based on `Mike Hamburg's work <https://eprint.iacr.org/2012/309.pdf>`_.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/generators/ECKeyPairGenerator.java#L94>`_ via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`_ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Derive:
 - Short-Weierstrass
 - `GLV if possible, else Window NAF <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L154>`_ via ``ECDHBasicAgreement.calculateAgreement -> ECPoint.multiply -> ECCurve.getMultiplier -> ECCurve.createDefaultMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`_ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/generators/ECKeyPairGenerator.java#L94>`_ via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`_ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Sign:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/signers/ECDSASigner.java#L237>`_ via
   ``ECDSASigner.generateSignature -> ECDSASigner.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`_ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Verify:
 - Short-Weierstrass
 - `Multi-scalar GLV if possible, else multi-scalar Window NAF with Shamir's trick <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECAlgorithms.java#L72>`_ via ``ECDSASigner.verifySignature -> ECAlgorithms.sumOfTwoMultiples``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`_ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

X25519
^^^^^^

KeyGen:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`_ via
   ``X25519.generatePublicKey -> X25519.scalarMultBase -> Ed25519.scalarMultBaseYZ -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Derive:
 - Montgomery
 - `Ladder <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L93>`_ via
   ``X25519.calculateAgreement -> X25519.scalarMult``.
 - `xz <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L68>`_.
 - `dbl-1987-m-3 <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L73>`_ and
   some `ladd-1987 <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L111>`_ formula.

Ed25519
^^^^^^^

KeyGen:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`_  via
   ``Ed25519.generatePublicKey -> Ed25519.scalarMultBaseEncoded -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Sign:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`_ via
   ``Ed25519.sign -> Ed25519.implSign -> Ed25519.scalarMultBaseEncoded -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Verify:
 - Twisted-Edwards
 - `Multi-scalar Window-NAF with Straus's trick <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L1329>`_ via
   ``Ed25519.verify -> Ed25519.implVerify -> Ed25519.scalarMultStraus128Var``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.


BoringSSL
=========

| Version: ``bfa8369`` (commit bfa8369)
| Repository: https://github.com/google/boringssl/
| Docs: https://commondatastorage.googleapis.com/chromium-boringssl-docs/headers.html

Primitives
----------

Supports P-224, P-256, P-384 and P-521.
Also Curve25519.
Uses fiat-crypto for the SECP curve field arithmetic.

P-224
^^^^^
 - Short-Weierstrass
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L995>`_ via ``mul_base -> ec_GFp_nistp224_point_mul_base``.
   `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L947C13-L947C38>`_ via ``mul -> ec_GFp_nistp224_point_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L580>`_,
 - Formulas unknown.

P-256
^^^^^
 - Short-Weierstrass
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L543>`_ via ``mul_base -> ec_GFp_nistp256_point_mul_base``.
   `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L476>`_ via ``mul -> ec_GFp_nistp256_point_mul``.
 - `Jacobian-3 <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L238>`_,
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L238>`_,
   `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L184>`_

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
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`_, via ``ec_GFp_mont_mul_base -> ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_
- `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`_

Derive:
 - Short-Weierstrass
 - ``ECDH_compute_key -> ec_point_mul_scalar -> meth.mul``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`_, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`_

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - ``EC_KEY_generate_key -> ec_point_mul_scalar_base -> meth.mul_base``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`_, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_
 - `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`_

Sign:
 - Short-Weierstrass
 - ``ECDSA_sign -> ECDSA_do_sign -> ecdsa_sign_impl -> ec_point_mul_scalar_base -> meth.mul_base``.
   Default: `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/simple_mul.c#L24>`_, via ``ec_GFp_mont_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_
- `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`_

Verify:
 - Short-Weierstrass
 - ``ECDSA_verify -> ECDSA_do_verify -> ecdsa_do_verify_no_self_test -> ec_point_mul_scalar_public -> meth.mul_public or meth.mul_public_batch``.
   Default: `Window NAF (w=4) based interleaving multi-exponentiation method <https://github.com/google/boringssl/blob/bfa8369/crypto/fipsmodule/ec/wnaf.c#L83>`_, via ``ec_GFp_mont_mul_public_batch``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_
- `add-2007-bl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L218>`_, `dbl-2001-b <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/ec_montgomery.c#L329>`_

X25519
^^^^^^

KeyGen:
 - Twisted-Edwards
 - ?? via ``X25519_keypair -> X25519_public_from_private -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`_: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`_, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`_

Derive:
 - Montgomery
 - Ladder via ``X25519 -> x25519_scalar_mult -> x25519_NEON/x25519_scalar_mult_adx/x25519_scalar_mult_generic``
 - Actually seems to use xz.
 - Unknown formula (ladder).

Ed25519
^^^^^^^
Based on ref10 of Ed25519.

KeyGen:
 - Twisted-Edwards
 - ?? via ``ED25519_keypair -> ED25519_keypair_from_seed -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`_: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`_, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`_

Sign:
 - Twisted-Edwards
 - ?? via ``ED25519_sign -> ED25519_keypair_from_seed -> x25519_ge_scalarmult_base``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`_: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`_, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`_

Verify:
 - Twisted-Edwards
 - Sliding window (signed) with interleaving? via ``ED25519_verify -> ge_double_scalarmult_vartime``.
 - Has `multiple coordinate systems <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/internal.h#L79>`_: projective, extended, completed, Duif
 - Unknown formulas. `dbl <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L617>`_, `add <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/curve25519/curve25519.c#L624>`_
