#!/usr/bin/env python
import click

from pyecsca.ec.mod import has_gmp
from pyecsca.ec.params import get_params
from pyecsca.misc.cfg import TemporaryConfig
from test.utils import Profiler


@click.command()
@click.option("-p", "--profiler", type=click.Choice(("py", "c")), default="py")
@click.option(
    "-m",
    "--mod",
    type=click.Choice(("python", "gmp")),
    default="gmp" if has_gmp else "python",
)
@click.option("-o", "--operations", type=click.INT, default=5000)
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
        p256 = get_params("secg", "secp256r1", "projective")
        coords = p256.curve.coordinate_model
        add = coords.formulas["add-2015-rcb"]
        dbl = coords.formulas["dbl-2015-rcb"]
        click.echo(
            f"Profiling {operations} {p256.curve.prime.bit_length()}-bit doubling formula (dbl2015rcb) executions..."
        )
        one_point = p256.generator
        with Profiler(
            profiler, directory, f"formula_dbl2016rcb_p256_{operations}_{mod}"
        ):
            for _ in range(operations):
                one_point = dbl(p256.curve.prime, one_point, **p256.curve.parameters)[0]
        click.echo(
            f"Profiling {operations} {p256.curve.prime.bit_length()}-bit addition formula (add2015rcb) executions..."
        )
        other_point = p256.generator
        with Profiler(
            profiler, directory, f"formula_add2016rcb_p256_{operations}_{mod}"
        ):
            for _ in range(operations):
                one_point = add(
                    p256.curve.prime, one_point, other_point, **p256.curve.parameters
                )[0]
        ed25519 = get_params("other", "Ed25519", "extended")
        ecoords = ed25519.curve.coordinate_model
        dblg = ecoords.formulas["mdbl-2008-hwcd"]
        click.echo(
            f"Profiling {operations} {ed25519.curve.prime.bit_length()}-bit doubling formula (mdbl2008hwcd) executions (with assumption)..."
        )
        eone_point = ed25519.generator
        with Profiler(
            profiler, directory, f"formula_mdbl2008hwcd_ed25519_{operations}_{mod}"
        ):
            for _ in range(operations):
                dblg(ed25519.curve.prime, eone_point, **ed25519.curve.parameters)


if __name__ == "__main__":
    main()
