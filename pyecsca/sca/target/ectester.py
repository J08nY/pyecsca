from abc import ABC
from binascii import hexlify
from enum import IntEnum, IntFlag
from functools import reduce
from math import ceil, log
from operator import or_
from typing import Optional, Mapping, List, Union

from public import public
from smartcard.CardConnection import CardConnection
from smartcard.Exceptions import CardConnectionException

from .ISO7816 import CommandAPDU, ResponseAPDU, ISO7816
from .PCSC import PCSCTarget
from ...ec.model import ShortWeierstrassModel
from ...ec.params import DomainParameters
from ...ec.point import Point


class ShiftableFlag(IntFlag):  # pragma: no cover
    def __lshift__(self, other):
        val = int(self) << other
        for e in self.__class__:
            if val == e.value:
                return e
        raise ValueError

    def __rshift__(self, other):
        val = int(self) >> other
        for e in self.__class__:
            if val == e.value:
                return e
        raise ValueError

    def __iter__(self):
        val = int(self)
        for e in self.__class__:
            i = int(e)
            if i & val == i:
                while i % 2 == 0 and i != 0:
                    i //= 2
                if i == 1:
                    yield e


@public
class KeypairEnum(ShiftableFlag):  # pragma: no cover
    KEYPAIR_LOCAL = 0x01
    KEYPAIR_REMOTE = 0x02
    KEYPAIR_BOTH = KEYPAIR_LOCAL | KEYPAIR_REMOTE


@public
class InstructionEnum(IntEnum):  # pragma: no cover
    INS_ALLOCATE = 0x5a
    INS_CLEAR = 0x5b
    INS_SET = 0x5c
    INS_TRANSFORM = 0x5d
    INS_GENERATE = 0x5e
    INS_EXPORT = 0x5f
    INS_ECDH = 0x70
    INS_ECDH_DIRECT = 0x71
    INS_ECDSA = 0x72
    INS_ECDSA_SIGN = 0x73
    INS_ECDSA_VERIFY = 0x74
    INS_CLEANUP = 0x75
    INS_ALLOCATE_KA = 0x76
    INS_ALLOCATE_SIG = 0x77
    INS_GET_INFO = 0x78
    INS_SET_DRY_RUN_MODE = 0x79
    INS_BUFFER = 0x7a
    INS_PERFORM = 0x7b


@public
class KeyBuildEnum(IntEnum):  # pragma: no cover
    BUILD_KEYPAIR = 0x01
    BUILD_KEYBUILDER = 0x02


@public
class ExportEnum(IntEnum):  # pragma: no cover
    EXPORT_TRUE = 0xff
    EXPORT_FALSE = 0x00

    @classmethod
    def from_bool(cls, val: bool):
        return cls.EXPORT_TRUE if val else cls.EXPORT_FALSE


@public
class RunModeEnum(IntEnum):  # pragma: no cover
    MODE_NORMAL = 0xaa
    MODE_DRY_RUN = 0xbb


@public
class KeyEnum(ShiftableFlag):  # pragma: no cover
    PUBLIC = 0x01
    PRIVATE = 0x02
    BOTH = PRIVATE | PUBLIC


@public
class AppletBaseEnum(IntEnum):  # pragma: no cover
    BASE_221 = 0x0221
    BASE_222 = 0x0222


@public
class KeyClassEnum(IntEnum):  # pragma: no cover
    ALG_EC_F2M = 4
    ALG_EC_FP = 5


@public
class KeyAgreementEnum(IntEnum):  # pragma: no cover
    ALG_EC_SVDP_DH = 1
    ALG_EC_SVDP_DH_KDF = 1
    ALG_EC_SVDP_DHC = 2
    ALG_EC_SVDP_DHC_KDF = 2
    ALG_EC_SVDP_DH_PLAIN = 3
    ALG_EC_SVDP_DHC_PLAIN = 4
    ALG_EC_PACE_GM = 5
    ALG_EC_SVDP_DH_PLAIN_XY = 6


@public
class SignatureEnum(IntEnum):  # pragma: no cover
    ALG_ECDSA_SHA = 17
    ALG_ECDSA_SHA_224 = 37
    ALG_ECDSA_SHA_256 = 33
    ALG_ECDSA_SHA_384 = 34
    ALG_ECDSA_SHA_512 = 38


@public
class TransformationEnum(ShiftableFlag):  # pragma: no cover
    NONE = 0x00
    FIXED = 0x01
    FULLRANDOM = 0x02
    ONEBYTERANDOM = 0x04
    ZERO = 0x08
    ONE = 0x10
    MAX = 0x20
    INCREMENT = 0x40
    INFINITY = 0x80
    COMPRESS = 0x0100
    COMPRESS_HYBRID = 0x0200
    MASK_04 = 0x0400


@public
class FormatEnum(IntEnum):  # pragma: no cover
    UNCOMPRESSED = 0
    COMPRESSED = 1
    HYBRID = 2


@public
class CurveEnum(IntEnum):  # pragma: no cover
    default = 0x00
    external = 0xff
    secp112r1 = 0x01
    secp128r1 = 0x02
    secp160r1 = 0x03
    secp192r1 = 0x04
    secp224r1 = 0x05
    secp256r1 = 0x06
    secp384r1 = 0x07
    secp521r1 = 0x08
    sect163r1 = 0x09
    sect233r1 = 0x0a
    sect283r1 = 0x0b
    sect409r1 = 0x0c
    sect571r1 = 0x0d


@public
class ParameterEnum(ShiftableFlag):  # pragma: no cover
    NONE = 0x00
    FP = 0x01
    F2M = 0x02
    A = 0x04
    B = 0x08
    G = 0x10
    R = 0x20
    K = 0x40
    W = 0x80
    S = 0x0100
    DOMAIN_FP = FP | A | B | G | R | K
    DOMAIN_F2M = F2M | A | B | G | R | K
    KEYPAIR = W | S
    ALL = FP | F2M | A | B | G | R | K | W | S


@public
class ChunkingException(Exception):  # pragma: no cover
    pass


class Response(ABC):  # pragma: no cover
    resp: ResponseAPDU
    sws: List[int]
    params: List[bytes]
    success: bool = True
    error: bool = False

    def __init__(self, resp: ResponseAPDU, num_sw: int, num_params: int):
        self.resp = resp
        self.sws = [0 for _ in range(num_sw)]
        self.params = [bytes() for _ in range(num_params)]

        offset = 0
        for i in range(num_sw):
            if len(resp.data) >= offset + 2:
                self.sws[i] = int.from_bytes(resp.data[offset:offset + 2], "big")
                offset += 2
                if self.sws[i] != ISO7816.SW_NO_ERROR:
                    self.success = False
            else:
                self.success = False
                self.error = True

        if self.resp.sw != ISO7816.SW_NO_ERROR:
            self.success = False
            self.error = False

        for i in range(num_params):
            if len(resp.data) < offset + 2:
                self.success = False
                self.error = True
                break
            param_len = int.from_bytes(resp.data[offset:offset + 2], "big")
            offset += 2
            if len(resp.data) < offset + param_len:
                self.success = False
                self.error = True
                break
            self.params[i] = resp.data[offset:offset + param_len]
            offset += param_len

    def __repr__(self):
        return f"{self.__class__.__name__}(sws=[{', '.join(list(map(hex, self.sws)))}], sw={hex(self.resp.sw)}, success={self.success}, error={self.error})"


@public
class AllocateKaResponse(Response):  # pragma: no cover
    """A response to the KeyAgreement allocation command."""

    def __init__(self, resp: ResponseAPDU):
        super().__init__(resp, 1, 0)


@public
class AllocateSigResponse(Response):  # pragma: no cover
    """A response to the Signature allocation command."""

    def __init__(self, resp: ResponseAPDU):
        super().__init__(resp, 1, 0)


@public
class AllocateResponse(Response):  # pragma: no cover
    """A response to the KeyPair allocation command."""

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum):
        super().__init__(resp, 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1, 0)


@public
class ClearResponse(Response):  # pragma: no cover
    """A response to the Clear key command."""

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum):
        super().__init__(resp, 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1, 0)


@public
class SetResponse(Response):  # pragma: no cover
    """A response to the Set command."""

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum):
        super().__init__(resp, 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1, 0)


@public
class TransformResponse(Response):  # pragma: no cover
    """A response to the Transform command."""

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum):
        super().__init__(resp, 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1, 0)


@public
class GenerateResponse(Response):  # pragma: no cover
    """A response to the Generate command."""

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum):
        super().__init__(resp, 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1, 0)


@public
class ExportResponse(Response):  # pragma: no cover
    """A response to the Export command, contains the exported parameters/values."""
    keypair: KeypairEnum
    key: KeyEnum
    parameters: ParameterEnum

    def __init__(self, resp: ResponseAPDU, keypair: KeypairEnum, key: KeyEnum,
                 params: ParameterEnum):
        self.keypair = keypair
        self.key = key
        self.parameters = params
        exported = 2 if keypair == KeypairEnum.KEYPAIR_BOTH else 1
        keys = 2 if key == KeyEnum.BOTH else 1
        param_count = 0
        param = ParameterEnum.FP
        while True:
            if param & params:
                param_count += 1
            if param == ParameterEnum.K:
                break
            param <<= 1
        other = 0
        other += 1 if key & KeyEnum.PUBLIC and params & ParameterEnum.W else 0
        other += 1 if key & KeyEnum.PRIVATE and params & ParameterEnum.S else 0
        super().__init__(resp, exported, exported * keys * param_count + exported * other)

    def get_index(self, keypair: KeypairEnum, param: ParameterEnum) -> Optional[int]:
        pair = KeypairEnum.KEYPAIR_LOCAL
        index = 0
        while True:
            mask = ParameterEnum.FP
            while True:
                if pair == keypair and param == mask:
                    return index
                if self.parameters & mask and self.keypair & pair:
                    if mask == ParameterEnum.W:
                        if self.key & KeyEnum.PUBLIC:
                            index += 1
                    elif mask == ParameterEnum.S:
                        if self.key & KeyEnum.PRIVATE:
                            index += 1
                    else:
                        index += 1
                if mask == ParameterEnum.S:
                    break
                mask <<= 1
            if pair == KeypairEnum.KEYPAIR_REMOTE:
                break
            pair <<= 1
        return None

    def get_param(self, keypair: KeypairEnum, param: ParameterEnum) -> Optional[bytes]:
        index = self.get_index(keypair, param)
        if index is not None:
            return self.params[index]
        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(sws=[{', '.join(list(map(hex, self.sws)))}], sw={hex(self.resp.sw)}, success={self.success}, error={self.error}, " \
               f"keypair={self.keypair.name}, key={self.key.name}, params={self.parameters.name})"


@public
class ECDHResponse(Response):  # pragma: no cover
    """A response to the ECDH and ECDH_direct KeyAgreement commands."""

    def __init__(self, resp: ResponseAPDU, export: bool):
        super().__init__(resp, 1, 1 if export else 0)

    @property
    def secret(self):
        if len(self.params) != 0:
            return self.params[0]
        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(sws=[{', '.join(list(map(hex, self.sws)))}], sw={hex(self.resp.sw)}, success={self.success}, error={self.error}, secret={hexlify(self.secret).decode() if self.secret else ''})"


@public
class ECDSAResponse(Response):  # pragma: no cover
    """A response to the ECDSA and ECDSA sign and ECDSA verify commands."""

    def __init__(self, resp: ResponseAPDU, export: bool):
        super().__init__(resp, 1, 1 if export else 0)

    @property
    def signature(self):
        if len(self.params) != 0:
            return self.params[0]
        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(sws=[{', '.join(list(map(hex, self.sws)))}], sw={hex(self.resp.sw)}, success={self.success}, error={self.error}, sig={hexlify(self.signature).decode() if self.signature else ''})"


@public
class CleanupResponse(Response):  # pragma: no cover
    """A response to the Cleanup command."""

    def __init__(self, resp: ResponseAPDU):
        super().__init__(resp, 1, 0)


@public
class RunModeResponse(Response):  # pragma: no cover
    """A response to the Set run mode command."""

    def __init__(self, resp: ResponseAPDU):
        super().__init__(resp, 1, 0)


class InfoResponse(Response):  # pragma: no cover
    """A response to the Info command, contains all information about the applet version/environment."""
    version: str
    base: AppletBaseEnum
    system_version: float
    object_deletion_supported: bool
    buf_len: int
    ram1_len: int
    ram2_len: int
    apdu_len: int

    def __init__(self, resp: ResponseAPDU):
        super().__init__(resp, 1, 0)

        offset = 2
        version_len = int.from_bytes(resp.data[offset:offset + 2], "big")
        offset += 2
        self.version = resp.data[offset:offset + version_len].decode()
        offset += version_len
        self.base = AppletBaseEnum(int.from_bytes(resp.data[offset:offset + 2], "big"))
        offset += 2
        system_version = int.from_bytes(resp.data[offset:offset + 2], "big")
        system_major = system_version >> 8
        system_minor = system_version & 0xff
        minor_size = 1 if system_minor == 0 else ceil(log(system_minor, 10))
        self.system_version = system_major + system_minor / (minor_size * 10)
        offset += 2
        self.object_deletion_supported = int.from_bytes(resp.data[offset:offset + 2], "big") == 1
        offset += 2
        self.buf_len = int.from_bytes(resp.data[offset:offset + 2], "big")
        offset += 2
        self.ram1_len = int.from_bytes(resp.data[offset:offset + 2], "big")
        offset += 2
        self.ram2_len = int.from_bytes(resp.data[offset:offset + 2], "big")
        offset += 2
        self.apdu_len = int.from_bytes(resp.data[offset:offset + 2], "big")
        offset += 2

    def __repr__(self):
        return f"{self.__class__.__name__}(sws=[{', '.join(list(map(hex, self.sws)))}], sw={hex(self.resp.sw)}, " \
               f"success={self.success}, error={self.error}, version={self.version}, base={self.base.name}, system_version={self.system_version}, " \
               f"object_deletion_supported={self.object_deletion_supported}, buf_len={self.buf_len}, ram1_len={self.ram1_len}, ram2_len={self.ram2_len}, apdu_len={self.apdu_len})"


@public
class ECTesterTarget(PCSCTarget):  # pragma: no cover
    """
    A smartcard target which communicates with the `ECTester <https://github.com/crocs-muni/ECTester>`_
    applet on smartcards of the JavaCard platform using PCSC.
    """
    CLA_ECTESTER = 0xb0
    AID_PREFIX = bytes([0x45, 0x43, 0x54, 0x65, 0x73, 0x74, 0x65, 0x72])
    AID_CURRENT_VERSION = bytes([0x30, 0x33, 0x33])  # Version v0.3.3
    AID_SUFFIX_221 = bytes([0x62])
    AID_SUFFIX_222 = bytes([0x78])

    chunking: bool

    def connect(self):
        self.chunking = False
        try:
            self.connection.connect(CardConnection.T1_protocol)
        except CardConnectionException:
            self.connection.connect(CardConnection.T0_protocol)
            self.chunking = True

    def send_apdu(self, apdu: CommandAPDU) -> ResponseAPDU:
        if self.chunking:
            data = bytes(apdu)
            num_chunks = (len(data) + 254) // 255
            for i in range(num_chunks):
                chunk_start = i * 255
                chunk_length = 255
                if chunk_start + chunk_length > len(data):
                    chunk_length = len(data) - chunk_start
                chunk = data[chunk_start: chunk_start + chunk_length]
                chunk_apdu = CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_BUFFER, 0, 0, chunk)
                resp = super().send_apdu(chunk_apdu)
                if resp.sw != 0x9000:
                    raise ChunkingException()
            apdu = CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_PERFORM, 0, 0)
        resp = super().send_apdu(apdu)
        if resp.sw & 0xff00 == ISO7816.SW_BYTES_REMAINING_00:
            resp = super().send_apdu(CommandAPDU(0x00, 0xc0, 0x00, 0x00, None, resp.sw & 0xff))
        return resp

    def select_applet(self, latest_version: bytes = AID_CURRENT_VERSION):
        """Select the *ECTester* applet, with a specified version or older."""
        version_bytes = bytearray(latest_version)
        for i in range(10):
            aid_222 = self.AID_PREFIX + version_bytes + self.AID_SUFFIX_222
            if self.select(aid_222):
                break
            else:
                aid_221 = self.AID_PREFIX + version_bytes + self.AID_SUFFIX_221
                if self.select(aid_221):
                    break
            # Count down by versions
            if version_bytes[2] == 0x30:
                if version_bytes[1] == 0x30:
                    if version_bytes[0] == 0x30:
                        return False
                    else:
                        version_bytes[0] -= 1
                        version_bytes[1] = 0x39
                        version_bytes[2] = 0x39
                else:
                    version_bytes[1] -= 1
                    version_bytes[2] = 0x39
            else:
                version_bytes[2] -= 1
        else:
            return False
        return True

    @staticmethod
    def encode_parameters(params: ParameterEnum, obj: Union[DomainParameters, Point, int]) -> Mapping[ParameterEnum, bytes]:
        """Encode values from `obj` into the byte parameters that the **ECTester** applet expects."""

        def convert_int(obj: int) -> bytes:
            ilen = (obj.bit_length() + 7) // 8
            return obj.to_bytes(ilen, "big")

        def convert_point(obj: Point) -> bytes:
            return bytes(obj)

        result = {}
        if isinstance(obj, DomainParameters) and isinstance(obj.curve.model, ShortWeierstrassModel):
            for param in params & ParameterEnum.DOMAIN_FP:
                if param == ParameterEnum.G:
                    result[param] = convert_point(obj.generator.to_affine())
                elif param == ParameterEnum.FP:
                    result[param] = convert_int(obj.curve.prime)
                elif param == ParameterEnum.A:
                    result[param] = convert_int(obj.curve.parameters["a"].x)
                elif param == ParameterEnum.B:
                    result[param] = convert_int(obj.curve.parameters["b"].x)
                elif param == ParameterEnum.R:
                    result[param] = convert_int(obj.order)
                elif param == ParameterEnum.K:
                    result[param] = convert_int(obj.cofactor)
        elif isinstance(obj, Point):
            for param in params & (ParameterEnum.G | ParameterEnum.W):
                result[param] = convert_point(obj)
        elif isinstance(obj, int):
            for param in params & ((ParameterEnum.DOMAIN_FP ^ ParameterEnum.G) | ParameterEnum.S):
                result[param] = convert_int(obj)
        else:
            raise TypeError
        return result

    def allocate_ka(self, ka_type: KeyAgreementEnum) -> AllocateKaResponse:
        """
        Send the Allocate KeyAgreement command.

        :param ka_type: Which KeyAgreement type to allocate.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ALLOCATE_KA, 0, 0,
                            bytes([ka_type])))
        return AllocateKaResponse(resp)

    def allocate_sig(self, sig_type: SignatureEnum) -> AllocateSigResponse:
        """
        Send the Allocate Signature command.

        :param sig_type: Which Signature type to allocate.
        :return: The response.
        """
        resp = self.send_apdu(CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ALLOCATE_SIG, 0, 0,
                                          bytes([sig_type])))
        return AllocateSigResponse(resp)

    def allocate(self, keypair: KeypairEnum, builder: KeyBuildEnum, key_length: int,
                 key_class: KeyClassEnum) -> AllocateResponse:
        """
        Send the Allocate KeyPair command.

        :param keypair: Which keypair to allocate.
        :param builder: Which builder to use to allocate the keypair.
        :param key_length: Bit-size of the allocated keypair.
        :param key_class: Type of the allocated keypair.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ALLOCATE, keypair, builder,
                            key_length.to_bytes(2, "big") + bytes([key_class])))
        return AllocateResponse(resp, keypair)

    def clear(self, keypair: KeypairEnum) -> ClearResponse:
        """
        Send the Clear key command.

        :param keypair: Which keypair to clear.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_CLEAR, keypair, 0, None))
        return ClearResponse(resp, keypair)

    def set(self, keypair: KeypairEnum, curve: CurveEnum, params: ParameterEnum,
            values: Optional[Mapping[ParameterEnum, bytes]] = None) -> SetResponse:
        """
        Send the Set command.

        :param keypair: Which keypair to set values on.
        :param curve: Which pre-set curve to use to set values, or default or external.
        :param params: Which parameters to set on the keypair.
        :param values: External values to set on the keypair.
        :return: The response.
        """
        if curve == CurveEnum.external and values is not None:
            if params != reduce(or_, values.keys()):
                raise ValueError("Params and values need to have the same keys.")
            payload = params.to_bytes(2, "big")
            e = ParameterEnum.FP
            while True:
                if e in values:
                    payload += len(values[e]).to_bytes(2, "big") + values[e]
                if e == ParameterEnum.S:
                    break
                e <<= 1
            resp = self.send_apdu(
                    CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_SET, keypair, curve,
                                payload))
        elif values is not None:
            raise ValueError("Values should be specified only if curve is external.")
        else:
            resp = self.send_apdu(
                    CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_SET, keypair, curve,
                                params.to_bytes(2, "big")))
        return SetResponse(resp, keypair)

    def transform(self, keypair: KeypairEnum, key: KeyEnum, params: ParameterEnum,
                  transformation: TransformationEnum) -> TransformResponse:
        """
        Send the Transform command.

        :param keypair: Which keypair to transform.
        :param key: Which key to apply the transform to.
        :param params: Which parameters to transform.
        :param transformation: What transformation to apply.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_TRANSFORM, keypair, key,
                            params.to_bytes(2, "big") + transformation.to_bytes(2, "big")))
        return TransformResponse(resp, keypair)

    def generate(self, keypair: KeypairEnum) -> GenerateResponse:
        """
        Send the Generate command.

        :param keypair: Which keypair to generate.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_GENERATE, keypair, 0, None))
        return GenerateResponse(resp, keypair)

    def export(self, keypair: KeypairEnum, key: KeyEnum, params: ParameterEnum) -> ExportResponse:
        """
        Send the Export command.

        :param keypair: Which keypair to export from.
        :param key: Which key to export from.
        :param params: Which parameters to export.
        :return: The response, containing the exported parameters.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_EXPORT, keypair, key,
                            params.to_bytes(2, "big")))
        return ExportResponse(resp, keypair, key, params)

    def ecdh(self, pubkey: KeypairEnum, privkey: KeypairEnum, export: bool,
             transformation: TransformationEnum, ka_type: KeyAgreementEnum) -> ECDHResponse:
        """
        Send the ECDH command.

        :param pubkey: Which keypair to use the pubkey from, in the key-agreement.
        :param privkey: Which keypair to use the privkey from, in the key-agreement.
        :param export: Whether to export the shared secret.
        :param transformation: The transformation to apply to the pubkey before key-agreement.
        :param ka_type: The key-agreement type to use.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ECDH, pubkey, privkey,
                            bytes([ExportEnum.from_bool(export)]) + transformation.to_bytes(
                                    2, "big") + bytes([ka_type])))
        return ECDHResponse(resp, export)

    def ecdh_direct(self, privkey: KeypairEnum, export: bool, transformation: TransformationEnum,
                    ka_type: KeyAgreementEnum, pubkey: bytes) -> ECDHResponse:
        """
        Send the ECDH direct command.

        :param privkey: Which keypair to use the privkey from, in the key-agreement.
        :param export: Whether to export the shared secret.
        :param transformation: The transformation to apply to the pubkey before key-agreement.
        :param ka_type: The key-agreement type to use.
        :param pubkey: The raw bytes that will be used as a pubkey in the key-agreement.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ECDH_DIRECT, privkey,
                            ExportEnum.from_bool(export),
                            transformation.to_bytes(2, "big") + bytes([ka_type]) + len(
                                    pubkey).to_bytes(2, "big") + pubkey))
        return ECDHResponse(resp, export)

    def ecdsa(self, keypair: KeypairEnum, export: bool, sig_type: SignatureEnum,
              data: bytes) -> ECDSAResponse:
        """
        Send the ECDSA command.

        :param keypair: The keypair to use.
        :param export: Whether to export the signature.
        :param sig_type: The Signature type to use.
        :param data: The data to sign and verify.
        :return: The response.
        """
        resp = self.send_apdu(CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ECDSA, keypair,
                                          ExportEnum.from_bool(export),
                                          bytes([sig_type]) + len(data).to_bytes(2, "big") + data))
        return ECDSAResponse(resp, export)

    def ecdsa_sign(self, keypair: KeypairEnum, export: bool, sig_type: SignatureEnum,
                   data: bytes) -> ECDSAResponse:
        """
        Send the ECDSA sign command.

        :param keypair: The keypair to use to sign.
        :param export: Whether to export the signature.
        :param sig_type: The Signature type to use.
        :param data: The data to sign.
        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ECDSA_SIGN, keypair,
                            ExportEnum.from_bool(export),
                            bytes([sig_type]) + len(data).to_bytes(2, "big") + data))
        return ECDSAResponse(resp, export)

    def ecdsa_verify(self, keypair: KeypairEnum, sig_type: SignatureEnum, sig: bytes,
                     data: bytes) -> ECDSAResponse:
        """
        Send the ECDSA verify command.

        :param keypair: The keypair to use to verify.
        :param sig_type: The Signature type to use.
        :param sig: The signature to verify.
        :param data: The data.
        :return: The response.
        """
        resp = self.send_apdu(CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_ECDSA_VERIFY,
                                          keypair, sig_type,
                                          len(data).to_bytes(2, "big") + data + len(sig).to_bytes(2,
                                                                                                  "big") + sig))
        return ECDSAResponse(resp, False)

    def cleanup(self) -> CleanupResponse:
        """
        Send the Cleanup command.

        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_CLEANUP, 0, 0, None))
        return CleanupResponse(resp)

    def info(self) -> InfoResponse:
        """
        Send the Info command.

        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_GET_INFO, 0, 0, None))
        return InfoResponse(resp)

    def run_mode(self, run_mode: RunModeEnum) -> RunModeResponse:
        """
        Send the Run mode command.

        :return: The response.
        """
        resp = self.send_apdu(
                CommandAPDU(self.CLA_ECTESTER, InstructionEnum.INS_SET_DRY_RUN_MODE, run_mode, 0,
                            None))
        return RunModeResponse(resp)
