#!/usr/bin/env python3
from setuptools import setup, find_namespace_packages

setup(
    name='pyecsca',
    author='Jan Jancar',
    author_email='johny@neuromancer.sk',
    version='0.2.0',
    url="https://neuromancer.sk/pyecsca/",
    packages=find_namespace_packages(include=["pyecsca.*"]),
    license="MIT",
    description="Python Elliptic Curve cryptography Side Channel Analysis toolkit.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research"
    ],
    package_data={
        "pyecsca.ec": ["efd/*/*", "efd/*/*/*", "efd/*/*/*/*", "std/*", "std/*/*"]
    },
    # install_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        "numpy==1.24.3",
        "scipy",
        "sympy>=1.7.1",
        "atpublic",
        "cython",
        "fastdtw",
        "asn1crypto",
        "h5py",
        "holoviews",
        "bokeh",
        "matplotlib",
        "datashader",
        "xarray",
        "astunparse",
        "numba==0.57.0"
    ],
    extras_require={
        "picoscope_sdk": ["picosdk"],
        "picoscope_alt": ["picoscope"],
        "chipwhisperer": ["chipwhisperer"],
        "smartcard": ["pyscard"],
        "leia": ["smartleia"],
        "gmp": ["gmpy2"],
        "dev": ["mypy", "flake8", "interrogate", "pyinstrument", "black", "types-setuptools"],
        "test": ["nose2", "parameterized", "coverage"],
        "doc": ["sphinx", "sphinx-autodoc-typehints", "nbsphinx", "sphinx-paramlinks", "sphinx_design"]
    }
)
