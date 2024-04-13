# ![](docs/_static/logo_black_full.png)

[![docs](https://img.shields.io/badge/docs-neuromancer.sk-brightgreen.svg)](https://neuromancer.sk/pyecsca/)  [![License MIT ](https://img.shields.io/github/license/J08nY/pyecsca?color=brightgreen)](https://github.com/J08nY/pyecsca/blob/master/LICENSE) ![Test](https://github.com/J08nY/pyecsca/workflows/Test/badge.svg) ![Lint](https://github.com/J08nY/pyecsca/workflows/Lint/badge.svg) [![Codecov](https://img.shields.io/codecov/c/gh/J08nY/pyecsca?color=brightgreen&logo=codecov)](https://codecov.io/gh/J08nY/pyecsca) ![](https://img.shields.io/static/v1?label=mypy&message=No%20issues&color=brightgreen) [![DeepSource](https://deepsource.io/gh/J08nY/pyecsca.svg/?label=active+issues&show_trend=true)](https://deepsource.io/gh/J08nY/pyecsca/?ref=repository-badge)

**Py**thon **E**lliptic **C**urve cryptography **S**ide-**C**hannel **A**nalysis toolkit.

For more info, see the [![docs](https://img.shields.io/badge/docs-neuromancer.sk-brightgreen.svg)](https://neuromancer.sk/pyecsca/).

## Functionality

**pyecsca** aims to fill a gap in SCA tooling for Elliptic Curve Cryptography, it focuses on
black-box implementations of ECC and presents a way to extract implementation information
about a black-box implementation of ECC through side-channels. The main goal of **pyecsca**
is to be able to reverse engineer the curve model, coordinate system, addition formulas, scalar
multiplier and even finite-field implementation details.

It currently provides:
 - Enumeration of millions of possible ECC implementation configurations (see [notebook/configuration_space](https://neuromancer.sk/pyecsca/notebook/configuration_space.html))
 - Simulation and execution tracing of key generation, ECDH and ECDSA (see [notebook/simulation](https://neuromancer.sk/pyecsca/notebook/simulation.html))
 - Synthesis of C implementations of ECC for embedded devices, given any implementation configuration (see [notebook/codegen](https://neuromancer.sk/pyecsca/notebook/codegen.html)),
   CPU-level simulation of implementations (see [notebook/simulator](https://neuromancer.sk/pyecsca/notebook/simulator.html))
 - Trace acquisition using PicoScope/ChipWhisperer oscilloscopes (see [notebook/measurement](https://neuromancer.sk/pyecsca/notebook/measurement.html))
 - Trace processing capabilities, e.g. signal-processing, filtering, averaging, cutting, aligning ([pyecsca.sca](https://neuromancer.sk/pyecsca/api/pyecsca.sca.html))
 - Trace visualization using holoviews and datashader (see [notebook/visualization](https://neuromancer.sk/pyecsca/notebook/visualization.html))
 - Communication via PCSC/LEIA with a smartcard target (see [notebook/smartcards](https://neuromancer.sk/pyecsca/notebook/smartcards.html))

**pyecsca** consists of three packages:
 - the core: https://github.com/J08nY/pyecsca
 - the codegen package: https://github.com/J08nY/pyecsca-codegen
 - the notebook package: https://github.com/J08nY/pyecsca-notebook

## Requirements

 - [Numpy](https://www.numpy.org/)
 - [Scipy](https://www.scipy.org/)
 - [sympy](https://sympy.org/)
 - [pandas](https://pandas.pydata.org/)
 - [atpublic](https://public.readthedocs.io/)
 - [fastdtw](https://github.com/slaypni/fastdtw)
 - [asn1crypto](https://github.com/wbond/asn1crypto)
 - [h5py](https://www.h5py.org/)
 - [holoviews](https://holoviews.org)
 - [bokeh](https://bokeh.org)
 - [datashader](https://datashader.org)
 - [matplotlib](https://matplotlib.org/)
 - [xarray](https://xarray.pydata.org/en/stable/)
 - [astunparse](https://astunparse.readthedocs.io/)
 - [numba](https://numba.pydata.org/)
 - **Optionally**:
   - **Oscilloscope support:**
     - [picosdk](https://github.com/picotech/picosdk-python-wrappers/)
     - [picoscope](https://github.com/colinoflynn/pico-python)
     - [chipwhisperer](https://github.com/newaetech/chipwhisperer)
   - **Smartcard support:**
     - [pyscard](https://pyscard.sourceforge.io/)
   - **LEIA support:**
     - [smartleia](https://pypi.org/project/smartleia/)
   - **Faster arithmetic:**
     - [gmpy2](https://gmpy2.readthedocs.io/) (and also GMP library)
     - [cypari2](https://cypari2.readthedocs.io/) (and also PARI library)

*pyecsca* contains data from the [Explicit-Formulas Database](https://www.hyperelliptic.org/EFD/index.html) by Daniel J. Bernstein and Tanja Lange.
The data was partially changed, to make working with it easier. It is available on Github at [crocs-muni/efd](https://github.com/crocs-muni/efd).

It uses [ChipWhisperer](https://chipwhisperer.com) as one of its targets. It also supports working with [Riscure](https://www.riscure.com) Inspector
trace sets, which are of a proprietary format.

### Testing & Development

See the [Makefile](Makefile) for tests, performance measurement, codestyle and type checking commands.
Use [black](https://github.com/psf/black) for code-formatting.

 - [pytest](https://pytest.org)
 - [mypy](http://mypy-lang.org/)
 - [flake8](https://flake8.pycqa.org/)
 - [coverage](https://coverage.readthedocs.io/)
 - [interrogate](https://interrogate.readthedocs.io/)
 - [pyinstrument](https://github.com/joerick/pyinstrument/)
 - [pre-commit](https://pre-commit.com/) at `.pre-commit-config.yaml`
 - [black](https://github.com/psf/black)

### Docs

 - [sphinx](https://www.sphinx-doc.org/)
 - [sphinx-autodoc-typehints](https://pypi.org/project/sphinx-autodoc-typehints/)
 - [nbsphinx](https://nbsphinx.readthedocs.io/)
 - [sphinx-paramlinks](https://pypi.org/project/sphinx-paramlinks/)
 - [sphinx-design](https://sphinx-design.readthedocs.io/)


## License

    MIT License

    Copyright (c) 2018-2024 Jan Jancar

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

Thanks alot to contributors: Tomas Jusko, Andrej Batora, Vojtech Suchanek and
to ChipWhisperer/NewAE.

*Development was supported by the Masaryk University grant [MUNI/C/1701/2018](https://www.muni.cz/en/research/projects/46834).*
