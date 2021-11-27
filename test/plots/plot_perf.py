#!/usr/bin/env python
import click

from pathlib import Path
import holoviews as hv
import numpy as np


@click.command()
@click.option(
    "-d",
    "--directory",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    envvar="DIR",
    required=True,
)
def main(directory):
    directory = Path(directory)
    for f in directory.glob("*.csv"):
        pname = str(f).removesuffix(".csv")
        d = np.genfromtxt(
            f,
            delimiter=",",
            dtype=None,
            encoding="ascii",
            names=("commit", "pyversion", "time"),
        )
        if len(d.shape) == 0:
            d.shape = (1,)
        line = hv.Curve(zip(d["commit"], d["time"]), "commit", "duration")
        hv.save(line, pname + ".svg", fmt="svg")


if __name__ == "__main__":
    main()
