from public import public
from scipy.stats import pearsonr
import numpy as np
from numpy.typing import NDArray

from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.point import Point
from pyecsca.ec.context import DefaultContext, local
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.mod import Mod
from pyecsca.sca.trace import Trace
from pyecsca.sca.trace.plot import plot_trace
from pyecsca.sca.attack.leakage_model import LeakageModel


@public
class CPA:
    traces: NDArray
    points: list[Point]
    mult: ScalarMultiplier
    params: DomainParameters
    leakage_model: LeakageModel
    correlations: dict[str, list[list[float]]]

    def __init__(
        self,
        points: list[Point],
        traces: list[Trace],
        leakage_model: LeakageModel,
        mult: ScalarMultiplier,
        params: DomainParameters,
    ):
        """
        :param points: Points on which scalar multiplication with secret scalar was performed
        :param traces: Power traces corresponding to the scalar multiplication for each of the points
        :param mult: Scalar multiplier used
        :param params: Domain parameters used
        """
        self.points = points
        self.traces = np.array([trace.samples for trace in traces]).transpose()
        self.mult = mult
        self.params = params
        self.leakage_model = leakage_model
        self.correlations = {"guess_one": [], "guess_zero": []}

    def compute_intermediate_value(
        self, guessed_scalar: int, target_bit: int, point: Point
    ) -> Mod:
        with local(DefaultContext()) as ctx:
            self.mult.init(self.params, point)
            self.mult.multiply(guessed_scalar)
        action_index = -1
        for bit in bin(guessed_scalar)[2 : target_bit + 2]:
            if bit == "1":
                action_index += 2
            elif bit == "0":
                action_index += 1
        result = ctx.actions[0].get_by_index([action_index]).action
        return result.output_points[0].X

    def compute_correlation_trace(
        self, guessed_scalar: int, target_bit: int
    ) -> list[float]:
        correlation_trace = []
        intermediate_values = []
        for i in range(len(self.points)):
            intermediate_value = self.compute_intermediate_value(
                guessed_scalar, target_bit, self.points[i]
            )
            intermediate_values.append(self.leakage_model(intermediate_value))
        for trace in self.traces:
            correlation_trace.append(pearsonr(intermediate_values, trace)[0])
        return correlation_trace

    def plot_correlations(self, ct):
        return plot_trace(Trace(np.array(ct))).opts(width=950, height=600)

    def recover_bit(
        self,
        recovered_scalar: int,
        target_bit: int,
        scalar_bit_length: int,
        real_pub_key: Point,
    ) -> int:
        if target_bit == scalar_bit_length - 1:
            self.mult.init(self.params, self.params.generator)
            if real_pub_key == self.mult.multiply(recovered_scalar):
                return recovered_scalar
            return recovered_scalar | 1
        mask = 1 << (scalar_bit_length - target_bit - 1)
        guessed_scalar_0 = recovered_scalar
        guessed_scalar_1 = recovered_scalar | mask
        correlation_trace_0 = self.compute_correlation_trace(
            guessed_scalar_0, target_bit
        )
        correlation_trace_1 = self.compute_correlation_trace(
            guessed_scalar_1, target_bit
        )
        self.correlations["guess_zero"].append(correlation_trace_0)
        self.correlations["guess_one"].append(correlation_trace_1)
        if np.nanmax(np.abs(correlation_trace_0)) > np.nanmax(
            np.abs(correlation_trace_1)
        ):
            return guessed_scalar_0
        return guessed_scalar_1

    def perform(self, scalar_bit_length: int, real_pub_key: Point) -> int:
        recovered_scalar = 1 << (scalar_bit_length - 1)
        for target_bit in range(1, scalar_bit_length):
            recovered_scalar = self.recover_bit(
                recovered_scalar, target_bit, scalar_bit_length, real_pub_key
            )
        return recovered_scalar
