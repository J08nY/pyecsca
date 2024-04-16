import numpy as np
import holoviews as hv
import matplotlib as mpl
import pytest

from pyecsca.sca.trace import Trace
from pyecsca.sca.trace.plot import (
    plot_trace,
    save_figure,
    save_figure_png,
    save_figure_svg,
    plot_traces,
)


@pytest.fixture()
def trace1():
    return Trace(np.array([6, 7, 3, -2, 5, 1], dtype=np.dtype("i1")))


@pytest.fixture()
def trace2():
    return Trace(np.array([2, 3, 7, 0, -1, 0], dtype=np.dtype("i1")))


def test_html(trace1, trace2, plot_path):
    hv.extension("bokeh")
    fig = plot_trace(trace1)
    save_figure(fig, str(plot_path()))
    other = plot_traces(trace1, trace2)
    save_figure(other, str(plot_path()))


@pytest.mark.skip("Broken")
def test_png(trace1, plot_path):
    hv.extension("matplotlib")
    mpl.use("agg")
    fig = plot_trace(trace1)
    save_figure_png(fig, str(plot_path()))


@pytest.mark.skip("Broken without some backend.")
def test_svg(trace1, plot_path):
    hv.extension("matplotlib")
    fig = plot_trace(trace1)
    save_figure_svg(fig, str(plot_path()))
