from pathlib import Path
import unittest
import json
from dataclasses import asdict

from pandas_tutor.parse import parse

test_cases = Path(__file__).parent / 'parse_golden'


class TestParse(unittest.TestCase):
    maxDiff = None
    pass


def make_test_case(test_name):
    in_file = test_cases / f'{test_name}.py'
    golden_file = test_cases / f'{test_name}.py.golden'

    def test(self: TestParse):
        self.assertTrue(in_file.exists())
        self.assertTrue(golden_file.exists())
        code = in_file.read_text()
        res = asdict(parse(code))
        golden_res = json.loads(golden_file.read_text())
        self.assertEqual(res, golden_res)

    return test


# make all test cases dynamically!
for test_name in test_cases.iterdir():
    if test_name.suffix == '.py' and test_name.name != '__init__.py':
        test_case = make_test_case(test_name.stem)
        setattr(TestParse, f'test_{test_name.stem}', test_case)
