#!/usr/bin/env python
import click

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
@click.option("-o", "--operations", type=click.INT, default=1000)
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

        scalar = 123456789123456789123456789123456789
        click.echo(
            f"Profiling {operations} {p128.curve.prime.bit_length()}-bit (k = {scalar}) multiples_computed computations..."
        )
        with Profiler(profiler, directory, f"epa_p128_ltr_{operations}_{mod}"):
            precomp_ctx, full_ctx, out = multiple_graph(
                scalar, p128, LTRMultiplier, LTRMultiplier
            )
            for _ in range(operations):
                check_inputs = graph_to_check_inputs(
                    precomp_ctx,
                    full_ctx,
                    out,
                    check_condition="necessary",
                    precomp_to_affine=True,
                    use_init=True,
                    use_multiply=True,
                )
                for _ in range(32):
                    evaluate_checks(
                        check_funcs={
                            "add": lambda x, y: False,
                            "affine": lambda x: False,
                        },
                        check_inputs=check_inputs,
                    )


if __name__ == "__main__":
    main()
