from typing import Dict

import pytest
from importlib_resources import files, as_file

import matplotlib.pyplot as plt

from pyecsca.sca import Trace

cases: Dict[str, int] = {}


@pytest.fixture()
def plot_name(request):
    def namer():
        test_name = f"{request.module.__name__}.{request.node.name}"
        case_id = cases.setdefault(test_name, 0) + 1
        cases[test_name] = case_id
        return test_name + str(case_id)
    return namer


@pytest.fixture()
def plot_path(plot_name):
    def namer():
        with as_file(files("test").joinpath("plots", plot_name())) as fname:
            return fname
    return namer


@pytest.fixture()
def plot(plot_path):
    def plotter(*traces: Trace, **kwtraces: Trace):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for i, trace in enumerate(traces):
            ax.plot(trace.samples, label=str(i))
        for name, trace in kwtraces.items():
            ax.plot(trace.samples, label=name)
        ax.legend(loc="best")
        fname = plot_path()
        plt.savefig(fname.parent / (fname.name + ".png"))
    return plotter
