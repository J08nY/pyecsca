from os import getenv

import numpy as np
import holoviews as hv
from pyecsca.sca.trace import Trace
from pyecsca.sca.trace.plot import (plot_trace, save_figure, save_figure_png, save_figure_svg,
                                    plot_traces)
from .utils import Plottable


class PlotTests(Plottable):

    def setUp(self) -> None:
        self.trace1 = Trace(np.array([6, 7, 3, -2, 5, 1], dtype=np.dtype("i1")), None, None)
        self.trace2 = Trace(np.array([2, 3, 7, 0, -1, 0], dtype=np.dtype("i1")), None, None)

    def test_html(self):
        if getenv("PYECSCA_TEST_PLOTS") is None:
            return
        hv.extension("bokeh")
        fig = plot_trace(self.trace1)
        save_figure(fig, self.get_fname())
        other = plot_traces(self.trace1, self.trace2)
        save_figure(other, self.get_fname())

    def test_png(self):
        if getenv("PYECSCA_TEST_PLOTS") is None:
            return
        hv.extension("matplotlib")
        fig = plot_trace(self.trace1)
        save_figure_png(fig, self.get_fname())

    def test_svg(self):
        if getenv("PYECSCA_TEST_PLOTS") is None:
            return
        hv.extension("matplotlib")
        fig = plot_trace(self.trace1)
        save_figure_svg(fig, self.get_fname())
