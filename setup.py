#!/usr/bin/env python3
from setuptools import setup, find_namespace_packages

setup(
        name='pyecsca',
        author='Jan Jancar',
        author_email='johny@neuromancer.sk',
        version='0.1.0',
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
            "Programming Language :: Python :: 3",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research"
        ],
        package_data={
            "pyecsca.ec" : ["efd/*/*", "efd/*/*/*", "efd/*/*/*/*", "std/*", "std/*/*"]
        },
        #install_package_data=True,
        python_requires='>=3.8',
        install_requires=[
            "numpy",
            "scipy",
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
            "gmpy2"
        ],
        extras_require={
            "picoscope_sdk": ["picosdk"],
            "picoscope_alt": ["picoscope"],
            "chipwhisperer": ["chipwhisperer"],
            "smartcard": ["pyscard"],
            "dev": ["mypy", "flake8"],
            "test": ["nose2", "parameterized", "green", "coverage"]
        }
)
