Go
==

| Version: ``go1.21.4``
| Repository: https://github.com/golang/go
| Docs:

Primitives
----------

ECDH, ECDSA over P-224, P-256, P-384 and P-521.
Ed25519, X25519

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Fixed window (w=4) <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/nistec/p224.go#L412>`__ (link points to P-224, but others are the same) via ``privateKeyToPublicKey -> ScalarBaseMult``
 - Projective
 - `add-2015-rcb <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/nistec/p224.go#L215>`__, `dbl-2015-rcb <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/nistec/p224.go#L270>`__

Derive:
 - Short-Weierstrass
 - `Fixed window (w=4) <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/nistec/p224.go#L342>`__ via ``ecdh -> ScalarMult``.
 - Same formulas as in Keygen.

Also supports constant-time, 64-bit assembly implementation of P256 described in https://eprint.iacr.org/2013/816.pdf

ECDSA
^^^^^

KeyGen:
 - Same as ECDH KeyGen via ``ecdsa.go:GenerateKey -> generateNISTEC -> randomPoint -> ScalarBaseMult``.

Sign:
 - Same as KeyGen via ``ecdsa.go:SignASN1 -> signNISTEC -> randomPoint -> ScalarBaseMult``.

Verify:
 - Two separate scalar multiplications ``ScalarBaseMult`` (same as KeyGen) and ``ScalarMult`` (same as ECDH Derive) via ``ecdsa.go:VerifyASN1 -> verifyNISTEC``.

X25519
^^^^^^

KeyGen:
 - Montgomery
 - `Ladder <https://github.com/golang/go/blob/go1.21.4/src/crypto/ecdh/x25519.go#L54>`__ via ``privateKeyToPublicKey -> x25519ScalarMult``.
 - xz
 - Unknown formula: `ladd-go-1214 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-go-1214.op3>`__

Derive:
 - Same as KeyGen via ``x25519.go:ecdh -> x25519ScalarMult``.

Ed25519
^^^^^^^

KeyGen:
 - Twisted-Edwards
 - Pippenger's signed 4-bit method with precomputation via ``ed25519.go:GenerateKey -> NewKeyFromSeed -> newKeyFromSeed -> ScalarBaseMult``.
 - `Extended coordinates <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/edwards25519/edwards25519.go#L28>`__ mixed with `y-x,y+x,2dxy <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/edwards25519/edwards25519.go#L52>`__ coordinates
 - `AddAffine <https://github.com/golang/go/blob/go1.21.4/src/crypto/internal/edwards25519/edwards25519.go#L312>`__ (and similar SubAffine)::

      YplusX.Add(&p.y, &p.x)
      YminusX.Subtract(&p.y, &p.x)

      PP.Multiply(&YplusX, &q.YplusX)
      MM.Multiply(&YminusX, &q.YminusX)
      TT2d.Multiply(&p.t, &q.T2d)

      Z2.Add(&p.z, &p.z)

      v.X.Subtract(&PP, &MM)
      v.Y.Add(&PP, &MM)
      v.Z.Add(&Z2, &TT2d)
      v.T.Subtract(&Z2, &TT2d)

Sign:
 - Same as Keygen via ``ed25519.go: Sign -> sign ->  ScalarBaseMult``.

Verify:
 - Bos-Coster method via ``ed25519.go: Verify -> verify -> VarTimeDoubleScalarBaseMult``.
 - Same coordinates and formulas as in Keygen.
