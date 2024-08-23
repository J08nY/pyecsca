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
 - `Simple Ladder <https://github.com/libressl/openbsd/blob/libressl-v3.8.2/src/lib/libcrypto/ec/ecp_smpl.c#L1305>`__ via ``kmethod.keygen -> ec_key_gen -> EC_POINT_mul -> method.mul_generator_ct -> ec_GFp_simple_mul_generator_ct -> ec_GFp_simple_mul_ct``.
   Also does coordinate blinding and fixes scalar bit-length.
 - Jacobian coordinates.
 - Unknown formulas: `add-libressl-v382 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-libressl-v382.op3>`__,
   `dbl-libressl-v382 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-libressl-v382.op3>`__

Derive:
 - Short-Weierstrass
 - `Simple Ladder <https://github.com/libressl/openbsd/blob/libressl-v3.8.2/src/lib/libcrypto/ec/ecp_smpl.c#L1305>`__ via ``kmethod.compute_key -> ecdh_compute_key -> EC_POINT_mul -> method.mul_single_ct -> ec_GFp_simple_mul_single_ct -> ec_GFp_simple_mul_ct``.
   Also does coordinate blinding and fixes scalar bit-length.
 - Same as KeyGen.


ECDSA
^^^^^

KeyGen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - `Simple Ladder <https://github.com/libressl/openbsd/blob/libressl-v3.8.2/src/lib/libcrypto/ec/ecp_smpl.c#L1305>`__ via ``ECDSA_sign -> kmethod.sign -> ecdsa_sign -> ECDSA_do_sign -> kmethod.sign_sig -> ecdsa_sign_sig -> ECDSA_sign_setup -> kmethod.sign_setup -> ecdsa_sign_setup -> EC_POINT_mul -> method.mul_generator_ct -> ec_GFp_simple_mul_generator_ct -> ec_GFp_simple_mul_ct``.
 - Same as ECDH.

Verify:
 - Short-Weierstrass
 - Window NAF interleaving multi-exponentiation method ``ECDSA_verify -> kmethod.verify -> ecdsa_verify -> ECDSA_do_verify -> kmethod.verify_sig -> ecdsa_verify_sig -> EC_POINT_mul -> method.mul_double_nonct -> ec_GFp_simple_mul_double_nonct -> ec_wNAF_mul``.
   Refers to http://www.informatik.tu-darmstadt.de/TI/Mitarbeiter/moeller.html#multiexp and https://www.informatik.tu-darmstadt.de/TI/Mitarbeiter/moeller.html#fastexp
 - Same coordinates and formulas as ECDH.


X25519
^^^^^^
Based on ref10 of Ed25519.
See :doc:`boringssl`. Not exactly the same.

Ed25519
^^^^^^^
Based on ref10 of Ed25519.
See :doc:`boringssl`. Not exactly the same.
