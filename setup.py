import betterjpeg
from setuptools import (find_packages, setup)

setup(
    name=betterjpeg.__pkgname__,
    description=betterjpeg.__description__,
    version=betterjpeg.__version__,
    packages=find_packages(),
    entry_points='''
        [console_scripts]
        betterjpeg=betterjpeg.betterjpeg:cli
    '''
)
