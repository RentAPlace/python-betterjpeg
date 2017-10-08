from setuptools import (find_packages, setup)

from rap import betterjpeg

setup(
    name=betterjpeg.__pkgname__,
    description=betterjpeg.__description__,
    version=betterjpeg.__version__,
    packages=["rap.betterjpeg"],
    entry_points="""
        [console_scripts]
        betterjpeg=rap.betterjpeg.betterjpeg:cli
    """
)
