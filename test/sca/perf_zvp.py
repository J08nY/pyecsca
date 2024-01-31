#!/usr/bin/env python
import click

from pyecsca.ec.mod import has_gmp
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.sca.re.zvp import zvp_points, map_to_affine
from pyecsca.ec.formula.unroll import unroll_formula
from pyecsca.ec.params import get_params
from test.utils import Profiler


@click.command()
@click.option("-p", "--profiler", type=click.Choice(("py", "c")), default="py")
@click.option(
    "-m",
    "--mod",
    type=click.Choice(("python", "gmp")),
    default="gmp" if has_gmp else "python",
)
@click.option("-o", "--operations", type=click.INT, default=1)
@click.option(
    "-d",
    "--directory",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    envvar="DIR",
)
def main(profiler, mod, operations, directory):
    with TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = mod
        p128 = get_params("secg", "secp128r1", "projective")
        formula = p128.curve.coordinate_model.formulas["add-2015-rcb"]
        unrolled = unroll_formula(formula)
        unrolled = map_to_affine(formula, unrolled)
        poly = unrolled[6][1]
        k = 5

        click.echo(
            f"Profiling {operations} {p128.curve.prime.bit_length()}-bit (k = {k}) ZVP computations..."
        )
        with Profiler(profiler, directory, f"zvp_p128_{operations}_{mod}"):
            for _ in range(operations):
                zvp_points(poly, p128.curve, k, p128.order)


if __name__ == "__main__":
    main()
