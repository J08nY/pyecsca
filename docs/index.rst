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
.. image:: https://img.shields.io/static/v1?label=mypy&message=No%20issues&color=brightgreen
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

**pyecsca** consists of three repositories:

.. grid:: 3

    .. grid-item-card::  Core

        The `core <https://github.com/J08nY/pyecsca>`_ package contains the core of the
        functionality, except the code generation and notebooks.

    .. grid-item-card::  Codegen

        The `codegen <https://github.com/J08nY/pyecsca-codegen>`_ package contains
        the code generation functionality.

    .. grid-item-card::  Notebook

        The `notebook <https://github.com/J08nY/pyecsca-notebook>`_ repository contains
        example notebooks that showcase functionality of the toolkit.


:fas:`book` Notebooks
=========================
The notebooks below contain a showcase of what is possible using **pyecsca** and
are the best source of documentation on how to use **pyecsca**.

.. toctree::
   :caption: Notebooks
   :titlesonly:
   :maxdepth: 1

   notebook/configuration_space
   notebook/simulation
   notebook/codegen
   notebook/emulator
   notebook/measurement
   notebook/visualization
   notebook/smartcards
   notebook/re/formulas
   notebook/re/rpa
   notebook/re/zvp
   notebook/re/epa


:fas:`code` API reference
=========================

.. toctree::
   :caption: API reference
   :titlesonly:
   :maxdepth: 3

   api/pyecsca.ec
   api/pyecsca.misc
   api/pyecsca.sca
   api/pyecsca.codegen

:fas:`file` Miscellaneous
=========================

.. toctree::
   :caption: Miscellaneous
   :titlesonly:
   :maxdepth: 1

   libraries
   references


Requirements
============

.. dropdown:: General

     - Numpy_
     - Scipy_
     - sympy_
     - pandas_
     - atpublic_
     - fastdtw_
     - asn1crypto_
     - h5py_
     - holoviews_
     - bokeh_
     - datashader_
     - matplotlib_
     - xarray_
     - astunparse_
     - numba_

     - **Optionally**:

       - **Oscilloscope support:**

         - picosdk_
         - picoscope_
         - chipwhisperer_
       - **Smartcard support:**

         - pyscard_
       - **LEIA support:**

         - leia_
       - **Faster arithmetic:**

         - gmpy2_ (and also GMP library)
         - cypari2_ (and also PARI library)

    *pyecsca* contains data from the `Explicit-Formulas Database`_ by Daniel J. Bernstein and Tanja Lange.
    The data was partially changed, to make working with it easier. It is available on Github at `crocs-muni/efd`_.

    It uses `ChipWhisperer`_ as one of its targets. It also supports working with Riscure_ Inspector trace sets, which are of a proprietary format.


.. dropdown:: Testing & Development

    See the Makefile for tests, performance measurement, codestyle and type checking commands.
    Use black_ for code-formatting.

     - pytest_
     - mypy_
     - flake8_
     - coverage_
     - interrogate_
     - pyinstrument_
     - pre-commit_
     - black_


.. dropdown:: Docs

     - sphinx_
     - sphinx-autodoc-typehints_
     - nbsphinx_
     - sphinx-paramlinks_
     - sphinx-design_

License
=======

.. dropdown:: MIT License

    MIT License

    Copyright (c) 2018-2023 Jan Jancar

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

.. _Numpy: https://www.numpy.org
.. _Scipy: https://www.scipy.org
.. _sympy: https://sympy.org/
.. _pandas: https://pandas.pydata.org/
.. _matplotlib: https://matplotlib.org/
.. _atpublic: https://public.readthedocs.io/
.. _fastdtw: https://github.com/slaypni/fastdtw
.. _asn1crypto: https://github.com/wbond/asn1crypto
.. _h5py: https://www.h5py.org/
.. _holoviews: https://holoviews.org
.. _bokeh: https://bokeh.org
.. _datashader: https://datashader.org
.. _xarray: https://xarray.pydata.org/en/stable/
.. _astunparse: https://astunparse.readthedocs.io/
.. _numba: https://numba.pydata.org/
.. _picosdk: https://github.com/picotech/picosdk-python-wrappers/
.. _picoscope: https://github.com/colinoflynn/pico-python
.. _pyscard: https://pyscard.sourceforge.io/
.. _leia: https://pypi.org/project/smartleia/
.. _gmpy2: https://gmpy2.readthedocs.io/
.. _cypari2: https://cypari2.readthedocs.io/
.. _pytest: https://pytest.org
.. _mypy: http://mypy-lang.org/
.. _flake8: https://flake8.pycqa.org/
.. _coverage: https://coverage.readthedocs.io/
.. _interrogate: https://interrogate.readthedocs.io/
.. _pyinstrument: https://github.com/joerick/pyinstrument/
.. _pre-commit: https://pre-commit.com
.. _black: https://github.com/psf/black
.. _sphinx: https://www.sphinx-doc.org/
.. _sphinx-autodoc-typehints: https://pypi.org/project/sphinx-autodoc-typehints/
.. _nbsphinx: https://nbsphinx.readthedocs.io/
.. _sphinx-paramlinks: https://pypi.org/project/sphinx-paramlinks/
.. _sphinx-design: https://pypi.org/project/sphinx_design/
.. _Explicit-Formulas Database: https://www.hyperelliptic.org/EFD/index.html
.. _crocs-muni/efd: https://github.com/crocs-muni/efd
.. _ChipWhisperer: https://chipwhisperer.com
.. _Riscure: https://www.riscure.com/
