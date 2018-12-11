import matplotlib.pyplot as plt
from unittest import TestCase
from pyecsca.sca import Trace
from os.path import join, exists
from os import mkdir, getenv


def slow(func):
    func.slow = 1
    return func


def plot(case: TestCase, *traces: Trace):
    if getenv("PYECSCA_TEST_PLOTS") is None:
        return
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, trace in enumerate(traces):
        ax.plot(trace.samples, label=str(i))
    ax.legend(loc="best")
    directory = join("test", "plots")
    if not exists(directory):
        mkdir(directory)
    plt.savefig(join(directory, case.id() + ".png"))
