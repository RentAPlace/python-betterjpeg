from setuptools import setup

setup(
    name='betterjpeg',
    version='0.0.1',
    py_modules=['betterjpeg'],
    entry_points='''
        [console_scripts]
        betterjpeg=betterjpeg:cli
    '''
)