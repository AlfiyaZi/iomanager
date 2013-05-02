from setuptools import setup

setup(
    name='iomanager',
    version='0.4.0',
    author='Josh Matthias',
    author_email='python.iomanager@gmail.com',
    packages=['iomanager'],
    scripts=[],
    url='https://github.com/jmatthias/iomanager',
    license='LICENSE.txt',
    description=('Guarantee structure and composition of input and output.'),
    long_description=open('README_pypi.txt').read(),
    install_requires=[
        "python-dateutil>=2.1",
        ],
    )