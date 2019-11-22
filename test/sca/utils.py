import matplotlib.pyplot as plt
from unittest import TestCase
from pyecsca.sca import Trace
from os.path import join, exists, split
from os import mkdir, getenv, getcwd


force_plot = True

def slow(func):
    func.slow = 1
    return func

cases = {}

def plot(case: TestCase, *traces: Trace, **kwtraces: Trace):
    if not force_plot and getenv("PYECSCA_TEST_PLOTS") is None:
        return
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, trace in enumerate(traces):
        ax.plot(trace.samples, label=str(i))
    for name, trace in kwtraces.items():
        ax.plot(trace.samples, label=name)
    ax.legend(loc="best")
    if split(getcwd())[1] == "test":
        directory = "plots"
    else:
        directory = join("test", "plots")
    if not exists(directory):
        mkdir(directory)
    case_id = cases.setdefault(case.id(), 0) + 1
    cases[case.id()] = case_id
    plt.savefig(join(directory, case.id() + str(case_id) + ".png"))
