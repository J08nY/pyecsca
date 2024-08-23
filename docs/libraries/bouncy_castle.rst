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
 - `Comb (w=6 for > 250 bits else w=5) <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/FixedPointCombMultiplier.java>`__
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
 - Formulas unknown: `add-bc-r1rv76-jac <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-bc-r1rv76-jac.op3>`__,
   `dbl-bc-r1rv76-jac <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-bc-r1rv76-jac.op3>`__,
   `add-bc-r1rv76-mod <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-bc-r1rv76-mod.op3>`__,
   `dbl-bc-r1rv76-mod <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-bc-r1rv76-mod.op3>`__

Derive:
 - Short-Weierstrass
 - `GLV if possible, else Window NAF <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L154>`__ via ``ECDHBasicAgreement.calculateAgreement -> ECPoint.multiply -> ECCurve.getMultiplier -> ECCurve.createDefaultMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas same as KeyGen.

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/generators/ECKeyPairGenerator.java#L94>`__ via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas same as KeyGen.

Sign:
 - Short-Weierstrass
 - `Comb <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/crypto/signers/ECDSASigner.java#L237>`__ via
   ``ECDSASigner.generateSignature -> ECDSASigner.createBasePointMultiplier``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas same as KeyGen.

Verify:
 - Short-Weierstrass
 - `Multi-scalar GLV if possible, else multi-scalar Window NAF with Shamir's trick <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECAlgorithms.java#L72>`__ via ``ECDSASigner.verifySignature -> ECAlgorithms.sumOfTwoMultiples``.
 - `Jacobian-Modified <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/ECCurve.java#L676>`__ via ``ECCurve.FP_DEFAULT_COORDS``.
   SECP curves use Jacobian, SECT curves use Lambda-Projective.
 - Formulas same as KeyGen.

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
 - Unknown formulas: `ladd-bc-r1rv76-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-bc-r1rv76-x25519.op3>`__,
   `dbl-bc-r1rv76-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-bc-r1rv76-x25519.op3>`__.
   Code: `dbl <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L73>`__ and `ladd <https://github.com/bcgit/bc-java/blob/r1rv76/core/src/main/java/org/bouncycastle/math/ec/rfc7748/X25519.java#L111>`__

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
