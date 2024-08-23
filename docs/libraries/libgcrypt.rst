libgcrypt
=========

| Version: ``1.10.2``
| Repository: https://git.gnupg.org/
| Docs: https://gnupg.org/documentation/manuals/gcrypt/

Primitives
----------

Supports ECDH, X25519 and EdDSA `on <https://gnupg.org/documentation/manuals/gcrypt/ECC-key-parameters.html#ECC-key-parameters>`__ C25519, X448, Ed25519, Ed448, NIST curves, Brainpool curves and secp256k1.
Also supports GOST and SM2 signatures.

ECDH
^^^^

KeyGen:
 - Short-Weierstrass
 - `Left to right double-and-add-always <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1824>`__ via ``gcry_pk_genkey -> _gcry_pk_genkey -> generate -> ecc_generate -> nist_generate_key -> _gcry_mpi_ec_mul_point``.
 - Jacobian coords
 - Unknown formulas: `add-libgcrypt-v1102 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/add-libgcrypt-v1102.op3>`__,
   `dbl-libgcrypt-v1102 <https://github.com/J08nY/pyecsca/blob/master/test/data/formulas/dbl-libgcrypt-v1102.op3>`__,

Derive:
 - Same as Keygen via ``gcry_pk_encrypt -> _gcry_pk_encrypt -> generate -> ecc_encrypt_raw -> _gcry_mpi_ec_mul_point``.


ECDSA
^^^^^

Keygen:
 - Same as ECDH.

Sign:
 - Same as Keygen via ``gcry_ecc_ecdsa_sign -> _gcry_ecc_ecdsa_sign -> _gcry_mpi_ec_mul_point``.

Verify:
 - Two separate scalar multiplications via ``gcry_ecc_ecdsa_verify -> _gcry_ecc_ecdsa_verify``.

EdDSA
^^^^^

Keygen:
 - Twisted-Edwards
 - `Left to right double-and-add-always <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1824>`__ via ``gcry_pk_genkey -> _gcry_pk_genkey -> generate -> ecc_generate -> _gcry_ecc_eddsa_genkey -> _gcry_mpi_ec_mul_point``.
 - Projective, `dbl-2008-bbjlp <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1314>`__ and `add-2008-bbjlp <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1563>`__

Sign:
 - Same as Keygen via ``gcry_ecc_eddsa_sign -> _gcry_ecc_eddsa_sign -> _gcry_mpi_ec_mul_point``.

Verify:
 - Two separate scalar multiplications via ``gcry_ecc_eddsa_verify -> _gcry_ecc_eddsa_verify``.


X25519
^^^^^^

KeyGen:
 - Montgomery
 - `Montgomery ladder <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1858>`__ via ``gcry_pk_genkey -> _gcry_pk_genkey -> generate -> ecc_generate -> nist_generate_key -> _gcry_mpi_ec_mul_point``.
 - xz coordinates with a shuffled version of `ladd-1987-m-3 <https://git.gnupg.org/cgi-bin/gitweb.cgi?p=libgcrypt.git;a=blob;f=mpi/ec.c;h=c24921eea8bea8363a503d6d6071b116c176d8e5;hb=1c5cbacf3d88dded5063e959ee68678ff7d0fa56#l1661>`__


Derive:
 - Same as Keygen via ``gcry_pk_encrypt -> _gcry_pk_encrypt -> generate -> ecc_encrypt_raw -> _gcry_mpi_ec_mul_point``.
