#!/usr/bin/env python
import click

from pyecsca.ec.mod import has_gmp
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import get_params
from pyecsca.misc.cfg import TemporaryConfig
from utils import Profiler


@click.command()
@click.option("-p", "--profiler", type=click.Choice(("py", "c")), default="py")
@click.option(
    "-m",
    "--mod",
    type=click.Choice(("python", "gmp")),
    default="gmp" if has_gmp else "python",
)
@click.option("-o", "--operations", type=click.INT, default=50)
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
        add = coords.formulas["add-2016-rcb"]
        dbl = coords.formulas["dbl-2016-rcb"]
        mult = LTRMultiplier(add, dbl)
        click.echo(
            f"Profiling {operations} {p256.curve.prime.bit_length()}-bit scalar multiplication executions..."
        )
        one_point = p256.generator
        with Profiler(profiler, directory, f"mult_ltr_rcb_p256_{operations}_{mod}"):
            for _ in range(operations):
                mult.init(p256, one_point)
                one_point = mult.multiply(
                    0x71A55E0C1ABB3A0E069419E0F837BC195F1B9545E69FC51E53C4D48D7FEA3B1A
                )
        # ed25519 = get_params("other", "Ed25519", "extended")
        # ecoords = ed25519.curve.coordinate_model
        # dblg = ecoords.formulas["mdbl-2008-hwcd"]
        # click.echo(f"Profiling {operations} {ed25519.curve.prime.bit_length()}-bit doubling formula executions (with assumption)...")
        # eone_point = ed25519.generator
        # with Profiler(profiler) as pr:
        #     for _ in range(operations):
        #         dblg(ed25519.curve.prime, eone_point, **ed25519.curve.parameters)


if __name__ == "__main__":
    main()
