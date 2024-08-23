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
 - `Fixed Window with FullPrecomputation (no doublings) (w=3) <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/point_mul.cpp#L78>`__, via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
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
 - `Fixed Window with FullPrecomputation (no doublings) (w=3) <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/point_mul.cpp#L78>`__, via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__

Sign:
 - Short-Weierstrass
 - `Fixed Window with FullPrecomputation (no doublings) (w=3) <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/point_mul.cpp#L78>`__, via ``blinded_base_point_multiply -> EC_Point_Base_Point_Precompute::mul``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__

Verify:
 - Short-Weierstrass
 - Multi-scalar (interleaved) fixed-window via ``ECDSA::verify -> EC_Point_Multi_Point_Precompute::multi_exp``.
 - `Jacobian <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__
 - `add-1998-cmo-2 <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L181>`__,
   `dbl-1986-cc <https://github.com/randombit/botan/blob/3.2.0/src/lib/pubkey/ec_group/ec_point.cpp#L278>`__

X25519
^^^^^^
Based on curve25519_donna.

 - Montgomery
 - Montgomery ladder (unrolled several iterations)
 - xz
 - Unknown formula: `ladd-botan-x25519 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/ladd-botan-x25519.op3>`__

Ed25519
^^^^^^^
Based on ref10 of Ed25519.
See :doc:`boringssl`.
