import contextlib
import io
import os
import unittest
from pathlib import Path

from pandas_tutor.__main__ import make_tutor_spec

test_cases = Path(__file__).parent / 'pg_wreck_it'


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # capture stdout and stderr to avoid cluttering test output.
        cls._stdout = io.StringIO()
        cls._context_stdout = contextlib.redirect_stdout(cls._stdout)

        cls._stderr = io.StringIO()
        cls._context_stderr = contextlib.redirect_stderr(cls._stderr)

        cls._context_stdout.__enter__()
        cls._context_stderr.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._context_stdout.__exit__(None, None, None)
        cls._context_stderr.__exit__(None, None, None)

        # we can print captured stdout and stderr if needed, in the future


def make_test_case(test_name):
    in_file = test_cases / f'{test_name}.py'
    golden_file = test_cases / f'{test_name}.py.golden'

    def test(self: TestEndToEnd):
        self.assertTrue(in_file.exists())
        self.assertTrue(golden_file.exists())

        code = in_file.read_text()

        # we'll just compare JSON strings here since we only apply special
        # encoding rules (e.g. NaN to None) after converting to JSON.
        res = make_tutor_spec(code)
        golden_res = golden_file.read_text().strip()

        self.assertEqual(res, golden_res)

    return test


# make all test cases dynamically!
for test_name in test_cases.iterdir():
    if test_name.suffix == '.py' and test_name.name != '__init__.py':
        if os.environ.get('CI', False) and test_name.stem.startswith('plot_'):
            # skip plotting test cases since gzipping isn't deterministic
            continue
        test_case = make_test_case(test_name.stem)
        setattr(TestEndToEnd, f'test_{test_name.stem}', test_case)
