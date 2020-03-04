"""
This module provides functions for plotting traces.
"""
from bokeh.io import show, save, export_png, export_svgs
from bokeh.layouts import column
from bokeh.plotting import Figure
from bokeh.resources import CDN
from public import public

from .trace import Trace


@public
def new_figure():
    return Figure()


@public
def show_figure(figure: Figure):
    show(figure)


@public
def save_figure(figure: Figure, fname: str, title: str):
    lay = column(figure, sizing_mode='stretch_both')
    save(lay, fname, resources=CDN, title=title)


@public
def save_figure_png(figure: Figure, fname: str, width: int, height: int):
    export_png(figure, fname, height, width)


@public
def save_figure_svg(figure: Figure, fname: str):
    lay = column(figure, sizing_mode='stretch_both')
    export_svgs(lay, fname)


@public
def plot_trace(figure: Figure, trace: Trace, **kwargs):
    figure.line(range(len(trace)), trace.samples, **kwargs)
