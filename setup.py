import betterjpeg
from setuptools import setup

setup(
    name=betterjpeg.__pkgname__,
    description=betterjpeg.__description__,
    version=betterjpeg.__version__,
    py_modules=['betterjpeg'],
    entry_points='''
        [console_scripts]
        betterjpeg=betterjpeg.betterjpeg:cli
    '''
)