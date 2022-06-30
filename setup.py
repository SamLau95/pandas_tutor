"""
put an empty __init__.py inside of every directory you want to include in the
wheel

to build a wheel, run this command, (important: make sure to rm -rf the build
cache):

rm -rf build/; python setup.py bdist_wheel
"""
# type: ignore

from setuptools import setup, find_packages

version = "2.0.2dev0"

# These packages are installed during pip install.
# Only packages that AREN'T bundled inline need to be listed here.
install_requires = [
    "pandas>=1.3,<2.0",
    "mypy-extensions==0.4.3",
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pandas_tutor",
    version=version,
    packages=find_packages(),
    install_requires=install_requires,
    package_data={
        "": ["*.golden"]
    },  # add all test .golden files into package along with .py files
    include_package_data=True,
)
