from os import mkdir, getenv, getcwd
from os.path import join, exists, split
from unittest import TestCase

import matplotlib.pyplot as plt

from pyecsca.sca import Trace

force_plot = True


def slow(func):
    func.slow = 1
    return func


def disabled(func):
    func.disabled = 1
    return func


cases = {}


class Plottable(TestCase):

    def get_dir(self):
        if split(getcwd())[1] == "test":
            directory = "plots"
        else:
            directory = join("test", "plots")
        if not exists(directory):
            mkdir(directory)
        return directory

    def get_fname(self):
        directory = self.get_dir()
        case_id = cases.setdefault(self.id(), 0) + 1
        cases[self.id()] = case_id
        return join(directory, self.id() + str(case_id))

    def plot(self, *traces: Trace, **kwtraces: Trace):
        if not force_plot and getenv("PYECSCA_TEST_PLOTS") is None:
            return
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for i, trace in enumerate(traces):
            ax.plot(trace.samples, label=str(i))
        for name, trace in kwtraces.items():
            ax.plot(trace.samples, label=name)
        ax.legend(loc="best")
        plt.savefig(self.get_fname() + ".png")
