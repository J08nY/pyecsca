from unittest import TestCase
import unittest

import numpy as np
from pyecsca.sca import (
    Trace,
    StackedTraces,
    GPUTraceManager,
    TraceSet,
    CombinedTrace
)

TPB = 128
TRACE_COUNT = 32
TRACE_LEN = 4 * TPB


class StackedCombineTests(TestCase):
    def setUp(self):
        self.samples = np.random.rand(TRACE_COUNT, TRACE_LEN)
        self.stacked_ts = StackedTraces(self.samples)

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
        self.assertTrue((stacked.samples == self.samples[:,:min_len]).all())
    
    def test_fromtraceset(self):
        max_len = self.samples.shape[1]
        min_len = max_len // 2
        traces = [
            Trace(t[min_len:np.random.randint(max_len)])
            for t
            in self.samples
        ]
        tset = TraceSet(*traces)
        min_len = min(map(len, traces))
        stacked = StackedTraces.fromtraceset(tset)

        self.assertIsInstance(stacked, StackedTraces)
        self.assertTupleEqual(
            stacked.samples.shape,
            (self.samples.shape[0], min_len)
        )
        self.assertTrue((stacked.samples == self.samples[:,:min_len]).all())
    
    def test_average(self):
        avg_trace = GPUTraceManager.average(self.stacked_ts)
        avg_cmp: np.ndarray = np.average(self.samples, 0)

        self.assertIsInstance(avg_trace, CombinedTrace)
        self.assertTupleEqual(
            avg_trace.samples.shape,
            avg_cmp.shape
        )
        self.assertTrue(all(np.isclose(avg_trace.samples, avg_cmp)))
    
    def test_standard_deviation(self):
        std_trace = GPUTraceManager.standard_deviation(self.stacked_ts)
        std_cmp: np.ndarray = np.std(self.samples, 0)

        self.assertIsInstance(std_trace, CombinedTrace)
        self.assertTupleEqual(
            std_trace.samples.shape,
            std_cmp.shape
        )
        self.assertTrue(all(np.isclose(std_trace.samples, std_cmp)))
    
    def test_variance(self):
        var_trace = GPUTraceManager.variance(self.stacked_ts)
        var_cmp: np.ndarray = np.var(self.samples, 0)

        self.assertIsInstance(var_trace, CombinedTrace)
        self.assertTupleEqual(
            var_trace.samples.shape,
            var_cmp.shape
        )
        self.assertTrue(all(np.isclose(var_trace.samples, var_cmp)))

    def test_average_and_variance(self):
        avg_trace, var_trace = GPUTraceManager.average_and_variance(self.stacked_ts)
        avg_cmp: np.ndarray = np.average(self.samples, 0)
        var_cmp: np.ndarray = np.var(self.samples, 0)

        self.assertIsInstance(avg_trace, CombinedTrace)
        self.assertIsInstance(var_trace, CombinedTrace)
        self.assertTupleEqual(
            avg_trace.samples.shape,
            avg_cmp.shape
        )
        self.assertTupleEqual(
            var_trace.samples.shape,
            var_cmp.shape
        )
        self.assertTrue(all(np.isclose(avg_trace.samples, avg_cmp)))
        self.assertTrue(all(np.isclose(var_trace.samples, var_cmp)))
