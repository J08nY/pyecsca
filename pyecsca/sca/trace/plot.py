"""
This module provides functions for plotting traces.
"""
from functools import reduce

import holoviews as hv
from holoviews.operation.datashader import datashade
from public import public

from .trace import Trace


@public
def save_figure(figure, fname: str):  # pragma: no cover
    hv.save(figure, fname + ".html", fmt="html")


@public
def save_figure_png(figure, fname: str):  # pragma: no cover
    hv.save(figure, fname + ".png", fmt="png")


@public
def save_figure_svg(figure, fname: str):  # pragma: no cover
    hv.save(figure, fname + ".svg", fmt="svg")


@public
def plot_trace(trace: Trace, **kwargs):  # pragma: no cover
    line = hv.Curve((range(len(trace)), trace.samples), kdims="x", vdims="y", **kwargs)
    return datashade(line, normalization="log")


@public
def plot_traces(*traces: Trace, **kwargs):  # pragma: no cover
    _cmaps = [
        ["lightblue", "darkblue"],
        ["lightcoral", "red"],
        ["lime", "green"],
        ["orange", "darkorange"],
        ["plum", "deeppink"],
        ["peru", "chocolate"],
        ["cyan", "darkcyan"]
    ]
    dss = []
    for i, trace in enumerate(traces):
        line = hv.Curve((range(len(trace)), trace.samples), kdims="x", vdims="y", **kwargs)
        dss.append(datashade(line, normalization="log", cmap=_cmaps[i % len(_cmaps)]))
    return reduce(lambda x, y: x * y, dss)
