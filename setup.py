"""
put an empty __init__.py inside of every directory you want to include in the
wheel

to build a wheel, run this command, (important: make sure to rm -rf the build
cache):

rm -rf build/; python setup.py bdist_wheel
"""
# type: ignore

from setuptools import setup, find_packages

version = "2.0.0.dev1"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# note that we don't put requirements.txt into the install_requires list
# since we bundle the dependencies directly into the wheel.

setup(
    name="pandas_tutor",
    version=version,
    packages=find_packages(),
    package_data={
        "": ["*.golden"]
    },  # add all test .golden files into package along with .py files
    include_package_data=True,
)
