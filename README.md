# ![](https://raw.githubusercontent.com/J08nY/pyecsca/master/docs/_static/logo_black_full.png)

[![docs](https://img.shields.io/badge/docs-pyecsca.org-black.svg)](https://pyecsca.org/)  [![License MIT ](https://img.shields.io/github/license/J08nY/pyecsca?color=brightgreen)](https://github.com/J08nY/pyecsca/blob/master/LICENSE) ![Test](https://github.com/J08nY/pyecsca/workflows/Test/badge.svg) ![Lint](https://github.com/J08nY/pyecsca/workflows/Lint/badge.svg) [![Codecov](https://img.shields.io/codecov/c/gh/J08nY/pyecsca?color=brightgreen&logo=codecov)](https://codecov.io/gh/J08nY/pyecsca) [![DeepSource](https://deepsource.io/gh/J08nY/pyecsca.svg/?label=active+issues&show_trend=true)](https://deepsource.io/gh/J08nY/pyecsca/?ref=repository-badge)

**Py**thon **E**lliptic **C**urve cryptography **S**ide-**C**hannel **A**nalysis toolkit.

For more info, see the [![docs](https://img.shields.io/badge/docs-pyecsca.org-black.svg)](https://pyecsca.org/).

## Functionality

**pyecsca** aims to fill a gap in SCA tooling for Elliptic Curve Cryptography, it focuses on
black-box implementations of ECC and presents a way to extract implementation information
about a black-box implementation of ECC through side-channels. The main goal of **pyecsca**
is to be able to reverse engineer the curve model, coordinate system, addition formulas, scalar
multiplier and even finite-field implementation details.

It currently provides:
 - Enumeration of millions of possible ECC implementation configurations (see [notebook/configuration_space](https://pyecsca.org/notebook/configuration_space.html))
 - Simulation and execution tracing of key generation, ECDH and ECDSA (see [notebook/simulation](https://pyecsca.org/notebook/simulation.html))
 - Synthesis of C implementations of ECC for embedded devices, given any implementation configuration (see [notebook/codegen](https://pyecsca.org/notebook/codegen.html)),
   CPU-level simulation of implementations (see [notebook/simulator](https://pyecsca.org/notebook/simulator.html))
 - Trace acquisition using PicoScope/ChipWhisperer oscilloscopes (see [notebook/measurement](https://pyecsca.org/notebook/measurement.html))
 - Trace processing capabilities, e.g. signal-processing, filtering, averaging, cutting, aligning ([pyecsca.sca](https://pyecsca.org/api/pyecsca.sca.html))
 - Trace visualization using holoviews and datashader (see [notebook/visualization](https://pyecsca.org/notebook/visualization.html))
 - Communication via PCSC/LEIA with a smartcard target (see [notebook/smartcards](https://pyecsca.org/notebook/smartcards.html))
 - Reverse-engineering of black-box ECC via RPA-RE and ZVP-RE methods (see [notebook/re/rpa](https://pyecsca.org/notebook/re/rpa.html) and [notebook/re/zvp](https://pyecsca.org/notebook/re/zvp.html))

**pyecsca** consists of three packages:
 - the core: https://github.com/J08nY/pyecsca
 - the codegen package: https://github.com/J08nY/pyecsca-codegen
 - the notebook package: https://github.com/J08nY/pyecsca-notebook

## Tutorials

To learn more about the toolkit you can check out two tutorials on it.
 - One from the [SummerSchool on Real-World Crypto and Privacy 2024](https://github.com/J08nY/pyecsca-tutorial-croatia2024) in Vodice, Croatia.
 - One from the [Cryptographic Hardware and Embedded Systems (CHES) 2024](https://github.com/J08nY/pyecsca-tutorial-ches2024) conference in Halifax, Canada.

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
*Development was supported by the AI-SecTools (VJ02010010) project.*
