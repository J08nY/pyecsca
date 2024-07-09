=================
pyecsca [pɪɛtska]
=================

.. image:: https://img.shields.io/badge/-Github-brightgreen?style=flat&logo=github
   :target: https://github.com/J08nY/pyecsca
.. image:: https://img.shields.io/github/license/J08nY/pyecsca?color=brightgreen
   :target: https://github.com/J08nY/pyecsca/blob/master/LICENSE
.. image:: https://github.com/J08nY/pyecsca/workflows/Test/badge.svg
   :target: https://github.com/J08nY/pyecsca/actions?query=workflow%3ATest
.. image:: https://github.com/J08nY/pyecsca/workflows/Lint/badge.svg
   :target: https://github.com/J08nY/pyecsca/actions?query=workflow%3ALint
.. image:: https://img.shields.io/codecov/c/gh/J08nY/pyecsca?color=brightgreen&logo=codecov
   :target: https://codecov.io/gh/J08nY/pyecsca
.. image:: https://deepsource.io/gh/J08nY/pyecsca.svg/?label=active+issues&show_trend=true
   :target: https://deepsource.io/gh/J08nY/pyecsca/?ref=repository-badge

**Py**\ thon **E**\ lliptic **C**\ urve cryptography **S**\ ide-**C**\ hannel **A**\ nalysis toolkit.

**pyecsca** aims to fill a gap in SCA tooling for Elliptic Curve Cryptography, it focuses on
black-box implementations of ECC and presents a way to extract implementation information
about a black-box implementation of ECC through side-channels. The main goal of **pyecsca**
is to be able to reverse engineer the curve model, coordinate system, addition formulas, scalar
multiplier and even finite-field implementation details.

It currently provides:

.. card:: Enumeration

    Enumeration of millions of possible ECC implementation configurations (see :doc:`notebook/configuration_space`)

.. card:: Simulation

    Simulation and execution tracing of key generation, ECDH and ECDSA (see :doc:`notebook/simulation`)

.. card:: Code generation

    Synthesis of C implementations of ECC for embedded devices, given any implementation configuration (see :doc:`notebook/codegen`),
    CPU-level emulation of implementations (see :doc:`notebook/emulator`)

.. card:: Trace acquisition

    Trace acquisition using PicoScope/ChipWhisperer oscilloscopes (see :doc:`notebook/measurement`)

.. card:: Trace processing

    Trace processing capabilities, e.g. signal-processing, filtering, averaging, cutting, aligning (:doc:`api/pyecsca.sca`)

.. card:: Trace visualization

    Trace visualization using holoviews and datashader (see :doc:`notebook/visualization`)

.. card:: Smartcard communication

    Communication via PCSC/LEIA with a smartcard target (see :doc:`notebook/smartcards`)

.. card:: Reverse-engineering

    Reverse-engineering of black-box ECC via RPA-RE and ZVP-RE methods (see :doc:`notebook/re/rpa` and :doc:`notebook/re/zvp`)

**pyecsca** consists of three repositories:

.. grid:: 1 1 3 3

    .. grid-item-card::  Core

        The `core <https://github.com/J08nY/pyecsca>`_ package contains the core of the
        functionality, except the code generation and notebooks.

    .. grid-item-card::  Codegen

        The `codegen <https://github.com/J08nY/pyecsca-codegen>`_ package contains
        the code generation functionality.

    .. grid-item-card::  Notebook

        The `notebook <https://github.com/J08nY/pyecsca-notebook>`_ repository contains
        example notebooks that showcase functionality of the toolkit.

.. toctree::
   :hidden:
   :titlesonly:
   :maxdepth: 2

   installation
   notebooks
   api
   libraries
   references


License
=======

.. dropdown:: MIT License

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

Development was supported by the Masaryk University grant `MUNI/C/1707/2018 <https://www.muni.cz/en/research/projects/46834>`_.
