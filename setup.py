from setuptools import setup

setup(
    name='IOProcess',
    version='0.1.0',
    author='Josh Matthias',
    author_email='python.ioprocess@gmail.com',
    packages=['ioprocess'],
    scripts=[],
    url='http://pypi.python.org/pypi/IOProcess/',
    license='LICENSE.txt',
    description=('Guarantee structure and composition of input and output.'),
    long_description=open('README.txt').read(),
    install_requires=[
        "python-dateutil>=2.1",
        ],
    )