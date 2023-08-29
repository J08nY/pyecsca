#!/usr/bin/env python
import sys

import click

from pyecsca.ec.divpoly import mult_by_n
from pyecsca.ec.params import get_params
from datetime import datetime


@click.command()
@click.option("-n", type=click.INT, default=21)
def main(n):
    p256 = get_params("secg", "secp256r1", "projective")

    print("Benchmarking divpoly computation on P-256...", file=sys.stderr)

    ns = []
    durs = []
    mems = []
    for i in range(2, n):
        start = datetime.now()
        mx, my = mult_by_n(p256.curve, i)
        end = datetime.now()
        duration = (end - start).total_seconds()
        memory = (mx[0].degree() + mx[1].degree() + my[0].degree() + my[1].degree()) * 32
        ns.append(i)
        durs.append((end - start).total_seconds())
        mems.append(memory)
        print(i, duration, memory, sep=",")


if __name__ == "__main__":
    main()
