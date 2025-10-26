#!/usr/bin/env python
import click

from pyecsca.ec.mod import Mod
from pyecsca.ec.mod.flint import has_flint
from pyecsca.ec.mod.gmp import has_gmp
from pyecsca.ec.params import get_params
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.sca.re.rpa import multiple_graph
from pyecsca.sca.re.epa import evaluate_checks, graph_to_check_inputs
from test.utils import Profiler


@click.command()
@click.option(
    "-p",
    "--profiler",
    type=click.Choice(("py", "c", "raw")),
    default="py",
    envvar="PROF",
)
@click.option(
    "-m",
    "--mod",
    type=click.Choice(("python", "gmp", "flint")),
    default="flint" if has_flint else "gmp" if has_gmp else "python",
    envvar="MOD",
)
@click.option("-o", "--operations", type=click.INT, default=100)
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

        scalars = [int(Mod.random(p128.order)) for _ in range(operations)]
        ops = [
            multiple_graph(scalar, p128, LTRMultiplier, LTRMultiplier)
            for scalar in scalars
        ]

        click.echo(
            f"Profiling {operations} {p128.curve.prime.bit_length()}-bit graph_to_check_inputs + evaluate_checks computations..."
        )
        with Profiler(profiler, directory, f"epa_p128_ltr_{operations}_{mod}"):
            for precomp_ctx, full_ctx, out in ops:
                check_inputs = graph_to_check_inputs(
                    precomp_ctx,
                    full_ctx,
                    out,
                    check_condition="all",
                    precomp_to_affine=True,
                    use_init=True,
                    use_multiply=True,
                    check_formulas={"add"},
                )
                c = 0
                for j in range(3220):
                    i = 0

                    def check_add(x, y):
                        nonlocal i, c
                        i += 1
                        c += 1
                        return (i % (30 * (j+1))) == 0

                    def check_affine(x):
                        return False

                    evaluate_checks(
                        check_funcs={
                            "add": check_add,
                            "affine": check_affine,
                        },
                        check_inputs=check_inputs,
                    )


if __name__ == "__main__":
    main()
