#!/usr/bin/env python3
from setuptools import setup

setup(
        name='pyecsca',
        author='Jan Jancar',
        author_email='johny@neuromancer.sk',
        version='0.1.0',
        packages=['pyecsca'],
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
        install_package_data=True,
        python_requires='>=3',
        install_requires=[
            "numpy",
            "scipy",
            "atpublic",
            "matplotlib",
            "fastdtw"
        ],
        extras_require={
            "typecheck": ["mypy"],
            "test": ["nose2", "parameterized","green", "coverage"]
        }
)
