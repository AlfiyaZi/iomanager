from setuptools import setup

setup(
    name='ioprocess',
    version='0.2.1',
    author='Josh Matthias',
    author_email='python.ioprocess@gmail.com',
    packages=['ioprocess'],
    scripts=[],
    url='https://github.com/jmatthias/IOProcess',
    license='LICENSE.txt',
    description=('Guarantee structure and composition of input and output.'),
    long_description=open('README.txt').read(),
    install_requires=[
        "python-dateutil>=2.1",
        ],
    )