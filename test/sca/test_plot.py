from os import getenv

import numpy as np

from pyecsca.sca.trace import Trace
from pyecsca.sca.trace.plot import (new_figure, plot_trace, save_figure, save_figure_png,
                                    save_figure_svg)
from .utils import Plottable, disabled


class PlotTests(Plottable):

    def setUp(self) -> None:
        self.trace = Trace(np.array([6, 7, 3, -2, 5, 1], dtype=np.dtype("i1")), None, None)
        self.fig = new_figure()
        plot_trace(self.fig, self.trace)

    def test_html(self):
        if getenv("PYECSCA_TEST_PLOTS") is None:
            return
        save_figure(self.fig, self.get_fname() + ".html", "Trace plot")

    @disabled
    def test_png(self):
        save_figure_png(self.fig, self.get_fname() + ".png", 1000, 400)

    @disabled
    def test_svg(self):
        save_figure_svg(self.fig, self.get_fname() + ".svg")
