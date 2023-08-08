#!/usr/bin/env python
import click

from importlib_resources import files, as_file
from test.utils import Profiler
import test.data.sca
from pyecsca.sca import (
    InspectorTraceSet,
    average,
    variance,
    standard_deviation,
    add,
    subtract,
    conditional_average,
)


@click.command()
@click.option("-p", "--profiler", type=click.Choice(("py", "c")), default="py")
@click.option("-o", "--operations", type=click.INT, default=100)
@click.option(
    "-d",
    "--directory",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    envvar="DIR",
)
def main(profiler, operations, directory):
    with as_file(files(test.data.sca).joinpath("example.trs")) as path:
        traces = InspectorTraceSet.read(path)
        with Profiler(profiler, directory, f"combine_average_example_{operations}"):
            for _ in range(operations):
                average(*traces)
        with Profiler(profiler, directory, f"combine_condavg_example_{operations}"):
            for _ in range(operations):
                conditional_average(*traces, condition=lambda trace: trace[0] > 0)
        with Profiler(profiler, directory, f"combine_variance_example_{operations}"):
            for _ in range(operations):
                variance(*traces)
        with Profiler(profiler, directory, f"combine_stddev_example_{operations}"):
            for _ in range(operations):
                standard_deviation(*traces)
        with Profiler(profiler, directory, f"combine_add_example_{operations}"):
            for _ in range(operations):
                add(*traces)
        with Profiler(profiler, directory, f"combine_subtract_example_{operations}"):
            for _ in range(operations):
                subtract(traces[0], traces[1])


if __name__ == "__main__":
    main()
