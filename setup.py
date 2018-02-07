"""
tidepool: process pool for running expensive computation.
"""

from setuptools import setup, find_packages

setup(
    name='tidepool',
    version='0.1.0',
    author='Zachary Balder',
    py_modules=['tidepool'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-benchmark'],
    packages=find_packages(exclude=[]),
)