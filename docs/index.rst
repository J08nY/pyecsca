=================
pyecsca [pɪɛtska]
=================

.. image:: https://img.shields.io/badge/-Github-brightgreen?style=flat&logo=github
   :target: https://github.com/J08nY/pyecsca
.. image:: https://img.shields.io/github/license/J08nY/pyecsca?color=brightgreen
   :target: https://github.com/J08nY/pyecsca/blob/master/LICENSE
.. image:: https://img.shields.io/travis/J08nY/pyecsca
   :target: https://travis-ci.com/J08nY/pyecsca
.. image:: https://img.shields.io/codecov/c/gh/J08nY/pyecsca?color=brightgreen&logo=codecov
   :target: https://codecov.io/gh/J08nY/pyecsca
.. image:: https://img.shields.io/static/v1?label=mypy&message=No%20issues&color=brightgreen

**Py**\ thon **E**\ lliptic **C**\ urve cryptography **S**\ ide-**C**\ hannel **A**\ nalysis toolkit.

**pyecsca** aims to fill a gap in SCA tooling for Elliptic Curve Cryptography, it focuses on
black-box implementations of ECC and presents a way to extract implementation information
about a black-box implementation of ECC through side-channels. The main goal of **pyecsca**
is to be able to reverse engineer the curve model, coordinate system, addition formulas, scalar
multiplier and even finite-field implementation details.

It is currently in an alpha stage of development and thus only provides:
 - Enumeration of millions of possible ECC implementation configurations (see :doc:`notebook/configuration_space`)
 - Simulation and execution tracing of key generation, ECDH and ECDSA (see :doc:`notebook/simulation`)
 - Synthesis of C implementations of ECC for embedded devices, given any implementation configuration (see :doc:`notebook/codegen`)
 - Trace acquisition using PicoScope/ChipWhisperer oscilloscopes (see :doc:`notebook/measurement`)
 - Trace processing capabilities, e.g. signal-processing, filtering, averaging, cutting, aligning (:doc:`api/pyecsca.sca`)
 - Trace visualization using holoviews and datashader (see :doc:`notebook/visualization`)

**pyecsca** consists of three packages:
 - the core: https://github.com/J08nY/pyecsca
 - the codegen package: https://github.com/J08nY/pyecsca-codegen
 - the notebook package: https://github.com/J08nY/pyecsca-notebook

Notebooks
=========
The notebooks below contain a showcase of what is possible using **pyecsca** and
are the best source of documentation on how to use **pyecsca**.

.. toctree::
   :titlesonly:
   :maxdepth: 1

   notebook/configuration_space
   notebook/simulation
   notebook/codegen
   notebook/measurement
   notebook/visualization

API reference
=============

.. toctree::
   :caption: API reference
   :titlesonly:
   :maxdepth: 3

   api/modules

Requirements
============

 - Numpy_
 - Scipy_
 - sympy_
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
 - **Optionally**:

   - **Oscilloscope support:**

     - picosdk_
     - picoscope_
     - chipwhisperer_
   - **Smartcard support:**

     - pyscard_

   - **Faster arithmetic:**

     - gmpy2_ (and also GMP library)

*pyecsca* contains data from the `Explicit-Formulas Database`_ by Daniel J. Bernstein and Tanja Lange.

It also supports working with Riscure_ Inspector trace sets, which are of a proprietary format.


Testing
-------

 - nose2_
 - green_
 - parameterized_
 - mypy_
 - flake8_
 - coverage_

Docs
----

 - sphinx_
 - sphinx-autodoc-typehints_
 - nbsphinx_

License
=======

    MIT License

    Copyright (c) 2018-2020 Jan Jancar

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

Development is supported by the Masaryk University grant `MUNI/C/1707/2018 <https://www.muni.cz/en/research/projects/46834>`_,
this support is very appreciated.

.. _Numpy: https://www.numpy.org
.. _Scipy: https://www.scipy.org
.. _sympy: https://sympy.org/
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
.. _picosdk: https://github.com/picotech/picosdk-python-wrappers/
.. _picoscope: https://github.com/colinoflynn/pico-python
.. _chipwhisperer: https://github.com/newaetech/chipwhisperer
.. _pyscard: https://pyscard.sourceforge.io/
.. _gmpy2: https://gmpy2.readthedocs.io/
.. _nose2: https://nose2.readthedocs.io
.. _green: https://github.com/CleanCut/green
.. _parameterized: https://github.com/wolever/parameterized
.. _mypy: http://mypy-lang.org/
.. _flake8: https://flake8.pycqa.org/
.. _coverage: https://coverage.readthedocs.io/
.. _sphinx: https://www.sphinx-doc.org/
.. _sphinx-autodoc-typehints: https://pypi.org/project/sphinx-autodoc-typehints/
.. _nbsphinx: https://nbsphinx.readthedocs.io/
.. _Explicit-Formulas Database: https://www.hyperelliptic.org/EFD/index.html
.. _Riscure: https://www.riscure.com/
