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
 - `Ladder (coZ, with subtraction) <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_make_key -> EccPoint_compute_public_key -> EccPoint_mult`` (also has coordinate randomization).
 - `Jacobian coZ coordinates (Z1 == Z2) <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L748>`__ from https://eprint.iacr.org/2011/338.pdf.
 - `coZ formulas <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L793>`__ from https://eprint.iacr.org/2011/338.pdf.

Derive:
 - Short-Weierstrass
 - `Ladder (coZ, with subtraction) <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_shared_secret -> EccPoint_compute_public_key -> EccPoint_mult`` (also has coordinate randomization).
 - Same coords and formulas as KeyGen.

ECDSA
^^^^^

Keygen:
 - Same as ECDH.

Sign:
 - Short-Weierstrass
 - `Ladder (coZ, with subtraction) <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L862>`__ via ``uECC_sign -> uECC_sign_with_k_internal -> EccPoint_mult`` (also has coordinate randomization).
 - Same coords and formulas as KeyGen.

Verify:
 - Short-Weierstrass
 - `Shamir's trick <https://github.com/kmackay/micro-ecc/blob/v1.1/uECC.c#L1558>`__ via ``uECC_verify``.
 - Same coords and formulas as KeyGen.
