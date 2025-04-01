#! /usr/bin/env python

from setuptools import setup


setup(
    name="adareducer",
    version="0.1",
    author="AdaCore",
    author_email="support@adacore.com",
    url="https://github.com/AdaCore/adareducer",
    description="Ada sources reducer for bug reproducers",
    install_requires=["libadalang"],
    packages=["ada_reducer"],
    entry_points={
        "console_scripts": [
            "adareducer = ada_reducer.main:main",
        ]
    },
)
