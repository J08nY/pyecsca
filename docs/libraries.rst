================
ECC in Libraries
================

.. contents:: Table of Contents
   :backlinks: none
   :depth: 1
   :local:

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

Lots of `scalarmults <https://github.com/bcgit/bc-java/tree/r1rv76/core/src/main/java/org/bouncycastle/math/ec>`__ available:
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/FixedPointCombMultiplier.java>`__
 - `GLV <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/GLVMultiplier.java>`__
 - `Window NAF L2R <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/WNafL2RMultiplier.java>`__
 - `Window "tau" NAF <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/WTauNafMultiplier.java>`__

Several `coordinate systems <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L27>`__ supported:
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

Ed25519 based on `Mike Hamburg's work <https://eprint.iacr.org/2012/309.pdf>`__.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/generators/ECKeyPairGenerator.java#L94>`__ via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Derive:
 - Short-Weierstrass
 - `GLV if possible, else Window NAF <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L154>`__ via ``ECDHBasicAgreement.calculateAgreement -> ECPoint.multiply -> ECCurve.getMultiplier -> ECCurve.createDefaultMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/generators/ECKeyPairGenerator.java#L94>`__ via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Sign:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/signers/ECDSASigner.java#L237>`__ via
   ``ECDSASigner.generateSignature -> ECDSASigner.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

Verify:
 - Short-Weierstrass
 - `Multi-scalar GLV if possible, else multi-scalar Window NAF with Shamir's trick <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECAlgorithms.java#L72>`__ via ``ECDSASigner.verifySignature -> ECAlgorithms.sumOfTwoMultiples``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas unknown.

X25519
^^^^^^

KeyGen:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`__ via
   ``X25519.generatePublicKey -> X25519.scalarMultBase -> Ed25519.scalarMultBaseYZ -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Derive:
 - Montgomery
 - `Ladder <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L93>`__ via
   ``X25519.calculateAgreement -> X25519.scalarMult``.
 - `xz <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L68>`__.
 - `dbl-1987-m-3 <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L73>`__ and
   some `ladd-1987 <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L111>`__ formula.

Ed25519
^^^^^^^

KeyGen:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`__  via
   ``Ed25519.generatePublicKey -> Ed25519.scalarMultBaseEncoded -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Sign:
 - Twisted-Edwards
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L92>`__ via
   ``Ed25519.sign -> Ed25519.implSign -> Ed25519.scalarMultBaseEncoded -> Ed25519.scalarMultBase``.
 - Many coordinate systems: Extended, half-Niels, affine.
 - Some HWCD formulas are used.

Verify:
 - Twisted-Edwards
 - `Multi-scalar Window-NAF with Straus's trick <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc8032/Ed25519.java#L1329>`__ via
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
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L995>`__ via ``mul_base -> ec_GFp_nistp224_point_mul_base``.
   `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L947C13-L947C38>`__ via ``mul -> ec_GFp_nistp224_point_mul``.
 - `Jacobian <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p224-64.c#L580>`__,
 - Formulas unknown.

P-256
^^^^^
 - Short-Weierstrass
 - `Comb <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L543>`__ via ``mul_base -> ec_GFp_nistp256_point_mul_base``.
   `Fixed Window <https://github.com/google/boringssl/blob/bfa8369795b7533a222a72b7a1bc928941cd66bf/crypto/fipsmodule/ec/p256.c#L476>`__ via ``mul -> ec_GFp_nistp256_point_mul``.
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
 - Actually seems to use xz.
 - Unknown formula (ladder).

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


Botan
=====

| Version: ``3.2.0`` (tag 3.2.0)
| Repository: https://github.com/randombit/botan/
| Docs: https://botan.randombit.net/handbook/

Primitives
----------

Has coordinate and scalar blinding,

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - Something like FullPrecomputation and Comb (no doublings), via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__

Derive:
 - Short-Weierstrass
 - Fixed Window (w=4) via ``blinded_var_point_multiply -> EC_Point_Var_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__,
   `dbl-1986-cc <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L278>`__

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - Something like FullPrecomputation and Comb (no doublings), via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__

Sign:
 - Short-Weierstrass
 - Something like FullPrecomputation and Comb (no doublings), via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__

Verify:
 - Short-Weierstrass
 - Multi-scalar (interleaved) (signed) fixed-window? via ``ECDSA::verify -> EC_Point_Multi_Point_Precompute::multi_exp``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__,
   `dbl-1986-cc <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L278>`__

X25519
^^^^^^
Based on curve2551_donna.

Ed25519
^^^^^^^
Based on ref10 of Ed255119.
See `BoringSSL`_.


SymCrypt
========

| Version: ``103.1.0`` (tag v103.1.0)
| Repository: https://github.com/microsoft/SymCrypt
| Docs:

Primitives
----------

Supports ECDH and ECDSA with `NIST <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_internal_curves.c#L16C19-L16C25>`__ curves (192, 224, 256, 384, 521) and Twisted Edwards `NUMS <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_internal_curves.c#L303>`__ curves (NumsP256t1, NumsP384t1, NumsP512t1).
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


fastecdsa
=========

| Version: ``v2.3.1``
| Repository: https://github.com/AntonKueltz/fastecdsa/
| Docs: https://fastecdsa.readthedocs.io/en/latest/index.html

Primitives
----------

Offers only ECDSA.
Supported `curves <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/fastecdsa/curve.py>`__: all SECP curves (8) for 192-256 bits, all (7) Brainpool curves as well as custom curves.


ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Ladder <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L124>`__ via ``get_public_key -> pointZZ_pMul``.
 -  Affine and schoolbook `add <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L68>`__ and `double <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L2>`__.

Sign:
 - Short-Weierstrass
 - Same ladder as Keygen via ``sign``.

Verify:
 - Short-Weierstrass
 - `Shamir's trick <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L163>`__ via ``verify -> pointZZ_pShamirsTrick``.


micro-ecc
=========

| Version: ``v1.1``
| Repository: https://github.com/kmackay/micro-ecc/
| Docs:

Primitives
----------

Offers ECDH and ECDSA on secp160r1, secp192r1, secp224r1, secp256r1, and secp256k1.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Montgomery ladder <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_make_key -> EccPoint_compute_public_key -> EccPoint_mult`` (also has coordinate randomization).
 - `Jacobian coZ coordinates (Z1 == Z2) <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L748>`__ from https://eprint.iacr.org/2011/338.pdf.
 - `coZ formulas <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L793>`__ from https://eprint.iacr.org/2011/338.pdf.

Derive:
 - Short-Weierstrass
 - `Montgomery ladder <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_shared_secret -> EccPoint_compute_public_key -> EccPoint_mult`` (also has coordinate randomization).
 - Same coords and formulas as KeyGen.

ECDSA
^^^^^

Keygen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - `Montgomery ladder <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_sign -> uECC_sign_with_k_internal -> EccPoint_mult`` (also has coordinate randomization).
 - Same coords and formulas as KeyGen.

Verify:
 - Short-Weierstrass
 - `Shamir's trick <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L1558>`__ via ``uECC_verify``.
 - Same coords and formulas as KeyGen.


Intel IPP cryptography
======================

| Version: ``2021.9.0``
| Repository: https://github.com/intel/ipp-crypto/
| Docs: https://www.intel.com/content/www/us/en/docs/ipp-crypto/developer-reference/2021-8/overview.html

Primitives
----------

Supports "ECC (NIST curves), ECDSA, ECDH, EC-SM2".
Also ECNR.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `(signed, Booth) Fixed Window with full precomputation? (width = 5) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_mulbase.c#L34>`__ via ``ippsGFpECPublicKey -> gfec_MulBasePoint -> gfec_base_point_mul or gfec_point_mul``.
    - Has special functions for NIST curves, but those implement the same scalarmult.
 - `Jacobian coords <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpecstuff.h#L76>`__
 - `add-1998-cmo-2 <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_add.c#L35>`__
   `dbl-1998-cmo-2 <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_dblpoint.c#L36>`__
 - Weirdly mentions "Enhanced Montgomery Multiplication" DOI:10.1155/2008/583926 in each of the formulas.
   Does actually use Montgomery arithmetic.

Derive:
 - Short-Weierstrass
 - `(signed, Booth) Fixed Window (width = 5) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_mul.c#L36>`__ via ``ippsGFpECSharedSecretDH -> gfec_MulPoint -> gfec_point_mul``.
 - Has special functions for NIST curves, but those implement the same scalarmult.
 - Same coordinates and formulas as KeyGen.

ECDSA
^^^^^

KeyGen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - `(signed, Booth) Fixed Window with full precomputation? (width = 5) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_mulbase.c#L34>`__ via ``ippsGFpECSignDSA -> gfec_MulBasePoint -> gfec_base_point_mul or gfec_point_mul``.
 - Same coordinates and formulas as KeyGen (and ECDH).

Verify:
 - Short-Weierstrass
 - `(signed, Booth) Fixed window (width = 5) interleaved multi-scalar <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/pcpgfpec_prod.c#L36>`__ via ``ippsGFpECVerifyDSA -> gfec_BasePointProduct -> either (gfec_base_point_mul + gfec_point_mul + gfec_point_add) or (gfec_point_prod)``.
 - Same coordinates and formulas as KeyGen (and ECDH).


x25519
^^^^^^

KeyGen:
 - Montgomery
 - `Some Full precomputation <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/crypto_mb/src/x25519/ifma_x25519.c#L1596>`__ via ``mbx_x25519_public_key``
 - xz
 - Unknown formulas.

Derive:
 - Montgomery
 - `? <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/crypto_mb/src/x25519/ifma_x25519.c#L1140>`__ via ``mbx_x25519 -> x25519_scalar_mul_dual``
 - xz
 - Unknown formulas.

Ed25519
^^^^^^^

KeyGen:
 - Twisted-Edwards
 - `Fixed window with full precomputation? (width = 4) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/crypto_mb/src/ed25519/ifma_arith_ed25519.c#L287>`__ via ``mbx_ed25519_public_key -> ifma_ed25519_mul_basepoint``
 - Mixes coordinate models::

    homogeneous: (X:Y:Z) satisfying x=X/Z, y=Y/Z
    extended homogeneous: (X:Y:Z:T) satisfying x=X/Z, y=Y/Z, XY=ZT
    completed: (X:Y:Z:T) satisfying x=X/Z, y=Y/T
    scalar precomputed group element: (y-x:y+x:2*t*d), t=x*y
    mb precomputed group element: (y-x:y+x:2*t*d), t=x*y
    projective flavor of the mb precomputed: (Y-X:Y+X:2*T*d:Z), T=X*Y

Add::

    fe52_add(r->X, p->Y, p->X);      // X3 = Y1+X1
    fe52_sub(r->Y, p->Y, p->X);      // Y3 = Y1-X1
    fe52_mul(r->Z, r->X, q->yaddx);  // Z3 = X3*yplusx2
    fe52_mul(r->Y, r->Y, q->ysubx);  // Y3 = Y3*yminisx2
    fe52_mul(r->T, q->t2d, p->T);    // T3 = T1*xy2d2
    fe52_add(t0, p->Z, p->Z);        // t0 = Z1+Z1
    fe52_sub(r->X, r->Z, r->Y);      // X3 = Z3-Y3 = X3*yplusx2 - Y3*yminisx2 = (Y1+X1)*yplusx2 - (Y1-X1)*yminisx2
    fe52_add(r->Y, r->Z, r->Y);      // Y3 = Z3+Y3 = X3*yplusx2 + Y3*yminisx2 = (Y1+X1)*yplusx2 + (Y1-X1)*yminisx2
    fe52_add(r->Z, t0, r->T);        // Z3 = 2*Z1 + T1*xy2d2
    fe52_sub(r->T, t0, r->T);        // T3 = 2*Z1 - T1*xy2d2

Dbl::

    fe52_sqr(r->X, p->X);
    fe52_sqr(r->Z, p->Y);
    fe52_sqr(r->T, p->Z);
    fe52_add(r->T, r->T, r->T);
    fe52_add(r->Y, p->X, p->Y);
    fe52_sqr(t0, r->Y);
    fe52_add(r->Y, r->Z, r->X);
    fe52_sub(r->Z, r->Z, r->X);
    fe52_sub(r->X, t0, r->Y);
    fe52_sub(r->T, r->T, r->Z);

Sign:
 - Twisted-Edwards
 - `Fixed window with full precomputation? (width = 4) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/crypto_mb/src/ed25519/ifma_arith_ed25519.c#L287>`__ via ``mbx_ed25519_sign -> ifma_ed25519_mul_basepoint``
 - Same as KeyGen.

Verify:
 - Twisted-Edwards
 - `Fixed window with full precomputation? (width = 4) <https://github.com/intel/ipp-crypto/blob/ippcp_2021.9.0/sources/ippcp/crypto_mb/src/ed25519/ifma_arith_ed25519.c#L287>`__ for base point mult, then just Fixed window (width = 4) for the other mult, all via ``mbx_ed25519_verify -> ifma_ed25519_prod_point -> ifma_ed25519_mul_point + ifma_ed25519_mul_basepoint``
 - Same as KeyGen.

LibreSSL
========

| Version: ``v3.8.2``
| Repository: https://github.com/libressl/portable
| Docs:

Primitives
----------

Supports ECDH, ECDSA as well as x25519 and Ed25519.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - Ladder via ``kmethod.keygen -> ec_key_gen -> EC_POINT_mul -> method.mul_generator_ct -> ec_GFp_simple_mul_generator_ct -> ec_GFp_simple_mul_ct``.
   Also does coordinate blinding and fixes scalar bit-length.
 - Jacobian coordinates.
 - `add-1998-hnm <https://github.com/libressl/openbsd/blob/libressl-v3.8.2/src/lib/libcrypto/ec/ecp_smpl.c#L472>`__ likely, due to the division by 2.

Dbl::

    n1 = 3 * X_a^2 + a_curve * Z_a^4
    Z_r = 2 * Y_a * Z_a
    n2 = 4 * X_a * Y_a^2
    X_r = n1^2 - 2 * n2
    n3 = 8 * Y_a^4
    Y_r = n1 * (n2 - X_r) - n3

Derive:
 - Short-Weierstrass
 - Ladder via ``kmethod.compute_key -> ecdh_compute_key -> EC_POINT_mul -> method.mul_single_ct -> ec_GFp_simple_mul_single_ct -> ec_GFp_simple_mul_ct``.
   Also does coordinate blinding and fixes scalar bit-length.
 - Same as KeyGen.


ECDSA
^^^^^

KeyGen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - Ladder via ``ECDSA_sign -> kmethod.sign -> ecdsa_sign -> ECDSA_do_sign -> kmethod.sign_sig -> ecdsa_sign_sig -> ECDSA_sign_setup -> kmethod.sign_setup -> ecdsa_sign_setup -> EC_POINT_mul -> method.mul_generator_ct -> ec_GFp_simple_mul_generator_ct -> ec_GFp_simple_mul_ct``.
 - Same as ECDH.

Verify:
 - Short-Weierstrass
 - Window NAF interleaving multi-exponentation method ``ECDSA_verify -> kmethod.verify -> ecdsa_verify -> ECDSA_do_verify -> kmethod.verify_sig -> ecdsa_verify_sig -> EC_POINT_mul -> method.mul_double_nonct -> ec_GFp_simple_mul_double_nonct -> ec_wNAF_mul``.
   Refers to http://www.informatik.tu-darmstadt.de/TI/Mitarbeiter/moeller.html#multiexp and https://www.informatik.tu-darmstadt.de/TI/Mitarbeiter/moeller.html#fastexp
 - Same coordinates and formulas as ECDH.


X25519
^^^^^^
Based on ref10 of Ed255119.
See `BoringSSL`_. Not exactly the same.

Ed25519
^^^^^^^
Based on ref10 of Ed255119.
See `BoringSSL`_. Not exactly the same.


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
 - `Sliding window <https://github.com/libtom/libtomcrypt/blob/v1.18.2/src/pk/ecc/ltc_ecc_mulmod_timing.c#L35>`__ via ``ecc_make_key -> ecc_make_key_ex -> ecc_ptmul -> ltc_ecc_mulmod_timing``.
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