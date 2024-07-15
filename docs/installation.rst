============================================
:fas:`screwdriver-wrench;fa-fw` Installation
============================================

Requirements
============

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
