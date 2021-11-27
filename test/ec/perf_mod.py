#!/usr/bin/env python
import click

from pyecsca.ec.mod import Mod, has_gmp
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
@click.option("-o", "--operations", type=click.INT, default=100000)
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
        n = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
        a = Mod(0x11111111111111111111111111111111, n)
        b = Mod(0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB, n)
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular inverse...")
        with Profiler(profiler, directory, f"mod_256b_inverse_{operations}_{mod}"):
            for _ in range(operations):
                a.inverse()
        click.echo(
            f"Profiling {operations} {n.bit_length()}-bit modular square root..."
        )
        with Profiler(profiler, directory, f"mod_256b_sqrt_{operations}_{mod}"):
            for _ in range(operations):
                a.sqrt()
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular multiply...")
        c = a
        with Profiler(profiler, directory, f"mod_256b_multiply_{operations}_{mod}"):
            for _ in range(operations):
                c = c * b
        click.echo(
            f"Profiling {operations} {n.bit_length()}-bit constant modular multiply..."
        )
        c = a
        with Profiler(
            profiler, directory, f"mod_256b_constmultiply_{operations}_{mod}"
        ):
            for _ in range(operations):
                c = c * 48006
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular square...")
        c = a
        with Profiler(profiler, directory, f"mod_256b_square_{operations}_{mod}"):
            for _ in range(operations):
                c = c ** 2
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular add...")
        c = a
        with Profiler(profiler, directory, f"mod_256b_add_{operations}_{mod}"):
            for _ in range(operations):
                c = c + b
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular subtract...")
        c = a
        with Profiler(profiler, directory, f"mod_256b_subtract_{operations}_{mod}"):
            for _ in range(operations):
                c = c - b
        click.echo(
            f"Profiling {operations} {n.bit_length()}-bit modular quadratic residue checks..."
        )
        with Profiler(profiler, directory, f"mod_256b_isresidue_{operations}_{mod}"):
            for _ in range(operations):
                a.is_residue()
        click.echo(f"Profiling {operations} {n.bit_length()}-bit modular random...")
        with Profiler(profiler, directory, f"mod_256b_random_{operations}_{mod}"):
            for _ in range(operations):
                Mod.random(n)


if __name__ == "__main__":
    main()
