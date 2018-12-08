#!/usr/bin/env python3
from setuptools import setup

setup(
    name='pyecsca',
    author='Jan Jancar',
    author_email='johny@neuromancer.sk',
    version='0.1.0',
    packages=['pyecsca'],
    license="MIT license",
    description="Python Elliptic Curve cryptography Side Channel Analysis toolkit.",
    long_description=open("README.md").read(),
    install_requires=[
        "numpy",
        "scipy",
        "atpublic",
        "matplotlib",
        "fastdtw"
    ],
    tests_require=[
        "nose2",
        "green"
    ]
)
