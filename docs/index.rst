=================
pyecsca [pɪɛtska]
=================

.. image:: https://img.shields.io/badge/-Github-brightgreen?style=flat&logo=github
   :target: https://github.com/J08nY/pyecsca
.. image:: https://img.shields.io/travis/J08nY/pyecsca
   :target: https://travis-ci.org/J08nY/pyecsca
.. image:: https://img.shields.io/github/license/J08nY/pyecsca.svg
   :target: https://github.com/J08nY/pyecsca/blob/master/LICENSE
.. image:: https://codecov.io/gh/J08nY/pyecsca/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/J08nY/pyecsca

**Py**\ thon **E**\ lliptic **C**\ urve cryptography **S**\ ide-**C**\ hannel **A**\ nalysis toolkit.

*pyecsca* aims to fill a gap in SCA tooling for Elliptic Curve Cryptography, it focuses on
black-box implementations of ECC and presents a way to extract implementation information
about a black-box implementation of ECC through side-channels. It is in an alpha stage of development
and thus currently only provides basic trace processing capabilities (in the *pyecsca.sca* package)
and ECC simulation in the *pyecsca.ec* package.


API
===

.. toctree::
   :titlesonly:
   :maxdepth: 3

   api/modules


Requirements
============

 - Numpy_
 - Scipy_
 - matplotlib_
 - atpublic_
 - fastdtw_
 - asn1crypto_

*pyecsca* contains data from the `Explicit-Formulas Database`_ by Daniel J. Bernstein and Tanja Lange.

It also supports working with Riscure_ Inspector trace sets, which are of a proprietary format.


Testing
-------

 - nose2_
 - green_
 - mypy_
 - coverage_

Docs
----

 - sphinx_
 - sphinx-autodoc-typehints_

License
=======

    MIT License

    Copyright (c) 2018-2019

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
.. _matplotlib: https://matplotlib.org/
.. _atpublic: https://public.readthedocs.io/
.. _fastdtw: https://github.com/slaypni/fastdtw
.. _asn1crypto: https://github.com/wbond/asn1crypto
.. _nose2: https://nose2.readthedocs.io
.. _green: https://github.com/CleanCut/green
.. _mypy: http://mypy-lang.org/
.. _coverage: https://coverage.readthedocs.io/
.. _sphinx: https://www.sphinx-doc.org/
.. _sphinx-autodoc-typehints: https://pypi.org/project/sphinx-autodoc-typehints/
.. _Explicit-Formulas Database: https://www.hyperelliptic.org/EFD/index.html
.. _Riscure: https://www.riscure.com/
