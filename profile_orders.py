import numpy as np
from numpy import random as npr
from pyecsca.sca.stacked_traces import GPUTraceManager
from pyecsca.sca.stacked_traces.stacked_traces import StackedTraces
from test.sca.perf_stacked_combine import (
    generate_dataset,
    report,
    timed,
)

NREPS = 100


def main():
    rm_times_storage = []
    cm_times_storage = []

    for _ in range(NREPS):
        rm_samples = generate_dataset(npr.default_rng(), 2 ** 10, 2 ** 15)
        rm_data = StackedTraces(rm_samples)
        rm_tm = GPUTraceManager(
            rm_data,
        )
        timed(rm_times_storage, log=True)(rm_tm.average)()

        cm_samples = np.array(rm_samples, order="F")
        cm_data = StackedTraces(cm_samples)
        cm_tm = GPUTraceManager(
            cm_data,
        )
        timed(cm_times_storage, log=True)(cm_tm.average)()

    rm_times = np.array([duration for _, duration in rm_times_storage[1:]])
    cm_times = np.array([duration for _, duration in cm_times_storage[1:]])
    print(f"Row major:\n\t{np.mean(rm_times) / 1e6:.3f}ms ± {np.std(rm_times) / 1e6:.3f}ms")
    print(f"Col major:\n\t{np.mean(cm_times) / 1e6:.3f}ms ± {np.std(cm_times) / 1e6:.3f}ms")


if __name__ == "__main__":
    main()
