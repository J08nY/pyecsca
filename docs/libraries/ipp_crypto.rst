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
 - Unknown formulas: `add-ipp-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-ipp-x25519.op3>`__, `dbl-ipp-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-ipp-x25519.op3>`__

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
