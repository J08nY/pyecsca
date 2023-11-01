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
============

| Version: ``103.1.0`` (tag v103.1.0)
| Repository: https://github.com/microsoft/SymCrypt
| Docs: 

Primitives
----------

Supports ECDH and ECDSA with `NIST <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_internal_curves.c#L16C19-L16C25>`__ curves (192, 224, 256, 384, 521) and Twisted Edwards `NUMS <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_internal_curves.c#L303>`__ curves (NumsP256t1, NumsP384t1, NumsP512t1).
Supports X25519.


ECDH
^^^^

KeyGen:
 - `Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcpointGenericSetRandom -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__. 
 - NIST use `Jacobian <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ecurve.c#L101>`__.
    - `jacobian-dbl-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L381>`__ for generic double via ``SymCryptEcpointDouble`` or a `tweak of  dbl-2007-bl/dbl-2001-b <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_short_weierstrass.c#L499>`__ formulae via ``SymCryptShortWeierstrassDoubleSpecializedAm3`` for ``a=-3``.
    - Tweak of `jacobian-add-2007-bl <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_short_weierstrass.c#L603>`__ via ``SymCryptEcpointAddDiffNonZero``. It also has side-channel unsafe version ``SymCryptShortWeierstrassAddSideChannelUnsafe`` and a generic wrapper for both via ``SymCryptEcpointAdd``.
 
 - NUMS curves use `Extended projective <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ecurve.c#L104>`__.
    - `dbl-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_twisted_edwards.c#L195>`__ via ``SymCryptTwistedEdwardsDouble``.
    - `add-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_twisted_edwards.c#L313>`__ via ``SymCryptTwistedEdwardsAdd`` or ``SymCryptTwistedEdwardsAddDiffNonZero``.

Derive:
 - `Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDhSecretAgreement -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__. 
 - Same coordinates and formulas as KeyGen


ECDSA
^^^^^

KeyGen:
 - `Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcpointGenericSetRandom -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__. 
 - NIST use `Jacobian <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ecurve.c#L101>`__.
    - `jacobian-dbl-2007-bl <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_short_weierstrass.c#L381>`__ for generic double via ``SymCryptEcpointDouble`` or a `tweak of  dbl-2007-bl/dbl-2001-b <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_short_weierstrass.c#L499>`__ formulae via ``SymCryptShortWeierstrassDoubleSpecializedAm3`` for ``a=-3``.
    - Tweak of `jacobian-add-2007-bl <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_short_weierstrass.c#L603>`__ via ``SymCryptEcpointAddDiffNonZero``. It also has side-channel unsafe version ``SymCryptShortWeierstrassAddSideChannelUnsafe`` and a generic wrapper for both via ``SymCryptEcpointAdd``.
 
 - NUMS curves use `Extended projective <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ecurve.c#L104>`__.
    - `dbl-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_twisted_edwards.c#L195>`__ via ``SymCryptTwistedEdwardsDouble``.
    - `add-2008-hwcd <https://github.com/microsoft/SymCrypt/blob/4d3fd5136855648d2a5e987f3b95473b056876b1/lib/ec_twisted_edwards.c#L313>`__ via ``SymCryptTwistedEdwardsAdd`` or ``SymCryptTwistedEdwardsAddDiffNonZero``.


Sign:
 - `Fixed-window <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDsaSignEx -> SymCryptEcpointScalarMul -> SymCryptEcpointScalarMulFixedWindow``. Algorithm 1 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__. 
 - Same coordinates and formulas as KeyGen

Verify:
 - `Double-scalar multiplication using the width-w NAF with interleaving <https://github.com/microsoft/SymCrypt/blob/v103.1.0/lib/ec_mul.c#L90>`__ via ``SymCryptEcDsaVerify > SymCryptEcpointMultiScalarMul -> SymCryptEcpointMultiScalarMulWnafWithInterleaving``. Algorithm 9 in `Selecting Elliptic Curves for Cryptography: An Efficiency and Security Analysis <https://eprint.iacr.org/2014/130.pdf>`__. 
 - Same coordinates and formulas as KeyGen

X25519
^^^^^^

KeyGen:
 - `Ladder <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_montgomery.c#L297>`__ via
   ``SymCryptMontgomeryPointScalarMul``.
 - `xz <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_montgomery.c#L173>`__.
 - `ladd-1987-m-3 <https://github.com/microsoft/SymCrypt/blob/b4f07a34bdb970e8690dc13a98fb9fb77edc0f50/lib/ec_montgomery.c#L151>`__  via ``SymCryptMontgomeryDoubleAndAdd``.


Derive:
 - Same as Keygen.


fastecdsa 
============

| Version: ``v2.3.1``
| Repository: https://github.com/AntonKueltz/fastecdsa/
| Docs: https://fastecdsa.readthedocs.io/en/latest/index.html

Primitives
----------

Offers only ECDSA. 
Supported `curves <https://github.com/AntonKueltz/fastecdsa/blob/main/fastecdsa/curve.py>`__: all SECP curves (8) for 192-256 bits, all (7) Brainpool curves as well as custom curves.


ECDSA
^^^^^

KeyGen:
 - `Ladder <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L124>`__ via ``get_public_key -> pointZZ_pMul``.
 -  Affine and schoolbook `add <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L68>`__ and `double <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L2>`__.

Sign:
 - Same ladder as Keygen via ``sign``. 

Verify:
 - `Shamir's trick <https://github.com/AntonKueltz/fastecdsa/blob/v2.3.1/src/curveMath.c#L163>`__ via ``verify -> pointZZ_pShamirsTrick``.