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
