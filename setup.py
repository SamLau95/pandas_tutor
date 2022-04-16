# type: ignore
'''
put an empty __init__.py inside of every directory you want to include in the wheel

to build a wheel, run this command, (important: make sure to rm -rf the build cache):

rm -rf build/; python setup.py bdist_wheel


TODO: maybe i don't need so many '# type: ignore' to stop mypy here? :0
''' # type: ignore

from setuptools import setup, find_packages

# maybe helpful? https://setuptools.pypa.io/en/latest/userguide/datafiles.html
setup( # type: ignore
    name='pandastutor',
    version='1.0',
    packages=find_packages(),
    package_data={"": ["*.golden"]}, # add all test .golden files into package along with .py files
    include_package_data=True,
) # type: ignore
