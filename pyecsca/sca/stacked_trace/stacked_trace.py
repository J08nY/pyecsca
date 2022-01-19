from audioop import avg
from numba import cuda, float32
import numpy as np
from public import public
from typing import Any, Iterable, Mapping, MutableSequence, Optional
from math import ceil, sqrt

TPB = 128


@public
class StackedTraces:
    """Samples of multiple traces and metadata"""

    meta: Mapping[str, Any]
    traces: np.ndarray

    def __init__(
                 self, traces: np.ndarray,
                 meta: Mapping[str, Any] = None) -> None:
        if meta is None:
            meta = dict()
        self.meta = meta
        self.traces = traces
    
    @classmethod
    def fromarray(cls, traces: MutableSequence[np.ndarray],
                  meta: Mapping[str, Any] = None) -> 'StackedTraces':
        min_samples = min(map(len, traces))
        for i, t in enumerate(traces):
            traces[i] = t[:min_samples]
        stacked = np.stack(traces)
        return cls(stacked, meta)
    
    @classmethod
    def fromtraceset(cls, traceset) -> 'StackedTraces':
        traces = [t.samples for t in traceset]
        return cls.fromarray(traces)
    
    def __len__(self):
        return self.traces.shape[0]

    def __getitem__(self, index):
        return self.traces
    
    def __iter__(self):
        yield from self.traces


class GPUTraceManager:
    @staticmethod
    def average(traces: StackedTraces) -> np.ndarray:
        samples = traces.traces
        samples_global = cuda.to_device(samples)
        device_result = cuda.device_array(samples.shape[1])

        tpb = TPB
        bpg = (samples.size + (tpb - 1)) // tpb

        gpu_average[bpg, tpb](samples_global, device_result)
        res = device_result.copy_to_host()
        return res
    
    def conditional_average(traces: StackedTraces) -> np.ndarray:
        raise NotImplementedError
    
    def standard_deviation(traces: StackedTraces) -> np.ndarray:
        samples = traces.traces
        samples_global = cuda.to_device(samples)
        device_result = cuda.device_array(samples.shape[1])

        tpb = TPB
        bpg = (samples.size + (tpb - 1)) // tpb

        gpu_std_dev[bpg, tpb](samples_global, device_result)
        res = device_result.copy_to_host()
        return res


@cuda.jit
def gpu_average(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return
    
    acc = 0.
    for row in range(samples.shape[0]):
        acc += samples[row, col]
    result[col] = acc / samples.shape[0]


@cuda.jit()
def gpu_std_dev(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    avg = 0.
    for row in range(samples.shape[0]):
        avg += samples[row, col]
    avg /= samples.shape[0]

    var = 0.
    for row in range(samples.shape[0]):
        current = samples[row, col] - avg
        var += current * current
    result[col] = sqrt(var / samples.shape[0])


@cuda.jit()
def gpu_variance(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)
    
    if col >= samples.shape[1]:
        return

    avg = 0.
    for row in range(samples.shape[0]):
        avg += samples[row, col]
    avg /= samples.shape[0]

    var = 0.
    for row in range(samples.shape[0]):
        current = samples[row, col] - avg
        var += current * current
    result[col] = var / samples.shape[0]


@cuda.jit()
def gpu_avg_var(samples: np.ndarray, result_avg: np.ndarray,
                result_var: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return
    
    avg = 0.
    for row in range(samples.shape[0]):
        avg += samples[row, col]
    avg /= samples.shape[0]

    var = 0.
    for row in range(samples.shape[0]):
        current = samples[row, col] - avg
        var += current * current
    result_avg[col] = avg
    result_var[col] = var


@cuda.jit()
def gpu_add(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return
    
    res = 0.
    for row in range(samples.shape[0]):
        res += samples[row, col]
    result[col] = res


@cuda.jit()
def gpu_subtract(samples_one: np.ndarray, samples_other: np.ndarray,
                 result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples_one.shape[1]:
        return
    
    result[col] = samples_one[col] - samples_other[col]


def test_average():
    samples = np.random.rand(4 * TPB, 8 * TPB)
    ts = StackedTraces.fromarray(np.array(samples))
    res = GPUTraceManager.average(ts)
    check_res = samples.sum(0) / ts.traces.shape[0]
    print(all(check_res == res))


def test_standard_deviation():
    samples: np.ndarray = np.random.rand(4 * TPB, 8 * TPB)
    ts = StackedTraces.fromarray(np.array(samples))
    res = GPUTraceManager.standard_deviation(ts)
    check_res = samples.std(0, dtype=samples.dtype)
    print(all(np.isclose(res, check_res)))


if __name__ == '__main__':
    test_average()
    test_standard_deviation()
