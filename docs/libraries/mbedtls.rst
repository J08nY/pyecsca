mbedTLS
=======

| Version: ``3.5.1``
| Repository: https://github.com/Mbed-TLS/mbedtls
| Docs: https://mbed-tls.readthedocs.io/en/latest/index.html

Primitives
----------

ECDH and ECDSA on P192, P224, P256, P384, P521 (their R and K variants) as well
as x25519 and x448.

x25519 has two implementations, and mbedTLS one (described below) and `one <https://github.com/Mbed-TLS/mbedtls/tree/v3.5.1/3rdparty/everest>`__ from
`Project Everest <https://github.com/project-everest/everest>`__.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ via ``mbedtls_ecdh_gen_public -> ecdh_gen_public_restartable -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_comb``.
   w = 5 for curves < 384 bits, then w = 6.
 - `Jacobian <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L1313>`__ coords with coordinate randomization.
 - `add-gecc-322 [GECC]_ algorithm 3.22 <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L1593>`__, `dbl-1998-cmo-2 <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L1496>`__. Also has alternative impl (``_ALT``).

Derive:
 - Short-Weierstrass
 - `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ via ``mbedtls_ecdh_compute_shared -> ecdh_compute_shared_restartable -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_comb``.
   w = 4 for curves < 384 bits, then w = 5. The width is smaller by 1 than the case when the generator point is used (in KeyGen).
 - Same coords and formulas as KeyGen.

ECDSA
^^^^^

KeyGen:
 - Short-Weierstrass
 - `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ via ``mbedtls_ecdsa_genkey -> mbedtls_ecp_gen_keypair -> mbedtls_ecp_gen_keypair_base -> mbedtls_ecp_mul -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_comb``.
 - Same as ECDH (KeyGen).

Sign:
 - Short-Weierstrass
 - `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ via ``mbedtls_ecdsa_sign -> mbedtls_ecdsa_sign_restartable -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_comb``.
 - Same as ECDH (KeyGen).

Verify:
 - Short-Weierstrass
 - `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ + `Comb <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2299>`__ via ``mbedtls_ecdsa_verify -> mbedtls_ecdsa_verify_restartable -> mbedtls_ecp_muladd_restartable -> mbedtls_ecp_mul_shortcuts + mbedtls_ecp_mul_shortcuts -> ecp_mul_restartable_internal -> ecp_mul_comb``.
 - Same as ECDH (KeyGen, Derive).

x25519
^^^^^^

KeyGen:
 - Montgomery
 - `Montgomery Ladder <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2555>`__ via ``mbedtls_ecdh_gen_public -> ecdh_gen_public_restartable -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_mxz``.
 - `xz <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2555>`__ coords.
 - `mladd-1987-m <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2509>`__.

Derive:
 - Montgomery
 - `Montgomery Ladder <https://github.com/Mbed-TLS/mbedtls/blob/v3.5.1/library/ecp.c#L2555>`__ via ``mbedtls_ecdh_compute_shared -> ecdh_compute_shared_restartable -> mbedtls_ecp_mul_restartable -> ecp_mul_restartable_internal -> ecp_mul_mxz``.
 - Same as KeyGen.
