from unittest import TestCase

import numpy as np
from pyecsca.sca import (
    Trace,
    StackedTraces,
    GPUTraceManager,
)


class StackedCombineTests(TestCase):
    def setUp(self):
        self.samples = np.random.rand(16, 32)
        self.st_traces = StackedTraces(self.samples)

    def test_fromarray(self):
        max_len = self.samples.shape[1]
        min_len = max_len // 2
        jagged_samples = [
            t[min_len:np.random.randint(max_len)]
            for t
            in self.samples
        ]
        min_len = min(map(len, jagged_samples))
        stacked = StackedTraces.fromarray(jagged_samples)

        self.assertIsInstance(stacked, StackedTraces)
        self.assertTupleEqual(
            stacked.samples.shape,
            (self.samples.shape[0], min_len)
        )
        self.assertTrue((stacked.samples, self.samples[:,:min_len]).all())
