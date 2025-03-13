import numpy as np
from typing import Optional, Tuple
from public import public

from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import CurveModel
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.key_agreement import ECDH
from pyecsca.ec.signature import Signature, SignatureResult
from pyecsca.ec.formula import FormulaAction
from pyecsca.ec.context import DefaultContext, local
from pyecsca.sca.attack import LeakageModel
from pyecsca.sca.trace import Trace
from pyecsca.sca.target.base import Target


@public
class LeakageTarget(Target):
    model: CurveModel
    coords: CoordinateModel
    mult: ScalarMultiplier
    leakage_model: LeakageModel
    params: Optional[DomainParameters]
    privkey: Optional[Mod]
    pubkey: Optional[Point]

    def __init__(
        self,
        model: CurveModel,
        coords: CoordinateModel,
        mult: ScalarMultiplier,
        leakage_model: LeakageModel,
    ):
        super().__init__()
        self.model = model
        self.coords = coords
        self.mult = mult
        self.leakage_model = leakage_model
        self.params = None
        self.privkey = None
        self.pubkey = None

    def get_trace(self, context: DefaultContext) -> Trace:
        def callback(action):
            if isinstance(action, FormulaAction):
                for intermediate in action.op_results:
                    leak = self.leakage_model(intermediate.value)
                    temp_trace.append(leak)

        temp_trace: list[int] = []
        if not context.actions:
            raise ValueError("Empty context")
        context.actions[0].walk(callback)
        return Trace(np.array(temp_trace))

    def simulate_scalar_mult_traces(
        self, num_of_traces: int, scalar: int
    ) -> Tuple[list[Point], list[Trace]]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        points = [
            self.params.curve.affine_random().to_model(self.coords, self.params.curve)
            for _ in range(num_of_traces)
        ]
        traces = []
        for point in points:
            _, trace = self.scalar_mult(scalar, point)
            traces.append(trace)
        return points, traces

    def simulate_ecdh_traces(
        self, num_of_traces: int
    ) -> Tuple[list[Point], list[Trace]]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        other_pubs = [
            self.params.curve.affine_random().to_model(self.coords, self.params.curve)
            for _ in range(num_of_traces)
        ]
        traces = []
        for pub in other_pubs:
            _, trace = self.ecdh(pub, None)
            traces.append(trace)
        return other_pubs, traces

    def set_params(self, params: DomainParameters) -> None:
        self.params = params

    def set_leakage_model(self, leakage_model: LeakageModel) -> None:
        self.leakage_model = leakage_model

    def scalar_mult(self, scalar: int, point: Point) -> Tuple[Point, Trace]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        with local(DefaultContext()) as ctx:
            self.mult.init(self.params, point)
            res_point = self.mult.multiply(scalar)
        return res_point, self.get_trace(ctx)

    def generate(self) -> Tuple[Tuple[Mod, Point], Trace]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        with local(DefaultContext()) as ctx:
            keygen = KeyGeneration(self.mult, self.params, False)
            priv, pub = keygen.generate()
        return (priv, pub), self.get_trace(ctx)

    def set_privkey(self, privkey: Mod) -> None:
        self.privkey = privkey

    def set_pubkey(self, pubkey: Point) -> None:
        self.pubkey = pubkey

    def ecdh(self, other_pubkey: Point, hash_algo=None) -> Tuple[bytes, Trace]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        if self.privkey is None:
            raise ValueError("Missing privkey")
        with local(DefaultContext()) as ctx:
            ecdh = ECDH(self.mult, self.params, other_pubkey, self.privkey, hash_algo)
            shared_secret = ecdh.perform()
        return shared_secret, self.get_trace(ctx)

    def ecdsa_sign(self, data: bytes, hash_algo=None) -> Tuple[SignatureResult, Trace]:
        if self.params is None:
            raise ValueError("Missing DomainParameters")
        if self.privkey is None:
            raise ValueError("Missing privkey")
        with local(DefaultContext()) as ctx:
            ecdsa = Signature(self.mult, self.params, self.mult.formulas["add"], self.pubkey, self.privkey, hash_algo)  # type: ignore
            signed_data = ecdsa.sign_data(data)
        return signed_data, self.get_trace(ctx)

    def ecdsa_verify(
        self, data: bytes, signature: SignatureResult, hash_algo=None
    ) -> Tuple[bool, Trace]:
        if self.params is None:
            raise ValueError
        if self.pubkey is None:
            raise ValueError("Missing pubkey")
        with local(DefaultContext()) as ctx:
            ecdsa = Signature(self.mult, self.params, self.mult.formulas["add"], self.pubkey, hash_algo)  # type: ignore
            verified = ecdsa.verify_data(signature, data)
        return verified, self.get_trace(ctx)

    def debug(self):
        return self.model.shortname, self.coords.name

    def connect(self):
        pass

    def disconnect(self):
        pass

    def set_trigger(self):
        pass

    def quit(self):
        pass
