from typing import Tuple, Dict
from public import public

from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.point import Point
from pyecsca.ec.context import DefaultContext, local
from pyecsca.ec.params import DomainParameters
from pyecsca.sca.trace import Trace
from pyecsca.sca.trace.combine import average, subtract
from pyecsca.sca.trace.process import absolute
from pyecsca.sca.trace.plot import plot_trace


@public
class DPA:
    traces: list[Trace]
    points: list[Point]
    mult: ScalarMultiplier
    params: DomainParameters
    doms: Dict[str, list[Trace]]

    def __init__(
        self,
        points: list[Point],
        traces: list[Trace],
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
        self.traces = traces
        self.mult = mult
        self.params = params
        self.doms = {"guess_one": [], "guess_zero": []}

    def compute_split_point(
        self, guessed_scalar: int, target_bit: int, point: Point
    ) -> Point:
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
        return result.output_points[0]

    def split_traces(
        self, guessed_scalar: int, target_bit: int
    ) -> Tuple[list[Trace], list[Trace]]:
        one_traces = []
        zero_traces = []
        for i in range(len(self.points)):
            # TODO: works only if the computed split point has "X" coordinate
            split_value = self.compute_split_point(
                guessed_scalar, target_bit, self.points[i]
            ).X
            if int(split_value) & 1 == 1:
                one_traces.append(self.traces[i])
            elif int(split_value) & 1 == 0:
                zero_traces.append(self.traces[i])
        return one_traces, zero_traces

    def calculate_difference_of_means(
        self, one_traces: list[Trace], zero_traces: list[Trace]
    ) -> Trace:
        avg_ones = average(*one_traces)
        avg_zeros = average(*zero_traces)
        return subtract(avg_ones, avg_zeros)  # type: ignore

    def plot_difference_of_means(self, dom):
        return plot_trace(dom).opts(width=950, height=600)

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
        ones_0, zeros_0 = self.split_traces(guessed_scalar_0, target_bit)
        ones_1, zeros_1 = self.split_traces(guessed_scalar_1, target_bit)
        dom_0 = self.calculate_difference_of_means(ones_0, zeros_0)
        dom_1 = self.calculate_difference_of_means(ones_1, zeros_1)
        self.doms["guess_zero"].append(dom_0)
        self.doms["guess_one"].append(dom_1)
        if max(absolute(dom_0)) > max(absolute(dom_1)):
            return guessed_scalar_0
        return guessed_scalar_1

    def perform(self, scalar_bit_length: int, real_pub_key: Point) -> int:
        recovered_scalar = 1 << (scalar_bit_length - 1)
        for target_bit in range(1, scalar_bit_length):
            recovered_scalar = self.recover_bit(
                recovered_scalar, target_bit, scalar_bit_length, real_pub_key
            )
        return recovered_scalar
