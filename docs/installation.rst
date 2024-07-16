============================================
:fas:`screwdriver-wrench;fa-fw` Installation
============================================

**pyecsca** consists of three repositories:

.. grid:: 1 1 3 3

    .. grid-item-card::  Core

        The `core <https://github.com/J08nY/pyecsca>`_ repository contains the core of the
        functionality, except the code generation and notebooks.

    .. grid-item-card::  Codegen

        The `codegen <https://github.com/J08nY/pyecsca-codegen>`_ repository contains
        the code generation functionality.

    .. grid-item-card::  Notebook

        The `notebook <https://github.com/J08nY/pyecsca-notebook>`_ repository contains
        example notebooks that showcase functionality of the toolkit.


Core
====

The core package can be installed either from `pypi <https://pypi.org/project/pyecsca/>`__ or from the
`source repository <https://github.com/J08nY/pyecsca>`__. There are several extras that can be installed:

- `picoscope_sdk` to enable support for PicoScope oscilloscopes using the picosdk_ package.
- `picoscope_alt` to enable support for PicoScope oscilloscopes using the picoscope_ package.
- `chipwhisperer` to enable support for ChipWhisperer_ targets and oscilloscopes.
- `smartcard` to enable support for smartcard targets using the pyscard_ package.
- `leia` to enable support for smartcard targets using the leia_ (smartleia) package.
- `gmp` to enable arithmetic via gmpy2_ (which may or may not be faster).
- `flint` to enable arithmetic via python-flint_ (which may or may not be faster).
- `pari` to enable faster division polynomial computation using cypari2_.
- `dev` to install several packages used in development.
- `test` to install several packages used for testing.
- `doc` to install several packages used for building documentation.

You can install these extras like this:

.. code-block:: shell

    pip install pyecsca[smartcard,gmp]

.. note::

    The core repository uses git submodules, make sure to check them out after cloning with: ``git submodule update --init``.


The core package contains data from the `Explicit-Formulas Database`_ by Daniel J. Bernstein and Tanja Lange.
The data was partially changed, to make working with it easier. It is available on Github at `crocs-muni/efd`_.

It uses `ChipWhisperer`_ as one of its targets. It also supports working with Riscure_ Inspector trace sets, which are of a proprietary format.

Optionally, you can Cythonize the ``pyecsca/ec/mod`` subpackage and sometimes gain a performance benefit, YMMV.

Requirements
------------

.. dropdown:: General
   :open:

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
         - python-flint_ (and also Flint library)
         - cypari2_ (and also PARI library)

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

Codegen
=======

The codegen package requires (and bundles in ``ext/libtommath`` as a git submodule) a version
of the libtommath library. The package can be either installed from `pypi <https://pypi.org/project/pyecsca-codegen/>`__ or from the
`source repository <https://github.com/J08nY/pyecsca-codegen>`__. Note that currently, the pypi project
contains the built package for x86_64 Linux only. Thus, installation from source is preferable.

Assuming you have ``make``, a C compiler and a C cross-compiler for ```arm-none-eabi`` you can just run:

.. code-block:: shell

    pip install .

inside the codegen repository and it should be built and installed automatically.

.. note::

    The codegen repository uses git submodules, make sure to check them out after cloning with: ``git submodule update --init``.

Notebooks
=========

The notebook repository is included as a submodule in the core repository.
However, this version can get outdated during active development. Note that
the notebooks have some additional requirements that are specified in the ``requirements.txt`` file,
which you can install with:

.. code-block:: shell

    pip install -r requirements.txt

inside the notebook repository.

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
.. _python-flint: https://fredrikj.net/python-flint/
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
