SunEC
=====

| Version: ``jdk-21-ga`` (JDK 21)
| Repository: https://github.com/openjdk/jdk/
| Docs:


Primitives
----------

ECDH, ECDSA, x25519, Ed25519

P-256
^^^^^

The only special thing is the generator scalarmult, ``Secp256R1GeneratorMultiplier`` which is a Comb.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - Fixed Window (width = 4) via ``ECKeyPairGenerator.generateKeyPair -> ECKeyPairGenerator.generateKeyPairImpl -> ECPrivateKeyImpl.calculatePublicKey -> ECOperations.multiply -> Default(PointMultiplier).pointMultiply``
 - projective-3 coords
 - RCB-based formulas: `add-sunec-v21 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-sunec-v21.op3>`__,
   `dbl-sunec-v21 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-sunec-v21.op3>`__,


Derive:
 - Same as KeyGen.

ECDSA
^^^^^

Same as ECDH.

x25519
^^^^^^

KeyGen:
 - Montgomery
 - Montgomery ladder
 - xz
 - Ladder formula from RFC 7748

Derive:
 - Same as KeyGen.

Ed25519
^^^^^^^

KeyGen:
 - Twisted-Edwards
 - Double and add always
 - Extended coords
 - Unknown formulas: `add-sunec-v21-ed25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-sunec-v21-ed25519.op3>`__,  `dbl-sunec-v21-ed25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-sunec-v21-ed25519.op3>`__

Sign:
 - Same as KeyGen.

Verify:
 - Same as KeyGen.
