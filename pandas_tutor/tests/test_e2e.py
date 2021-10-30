from pathlib import Path
import unittest
import json

from ..main import make_tutor_spec_py

test_cases = Path(__file__).parent / 'e2e_golden'


class TestEndToEnd(unittest.TestCase):
    maxDiff = None
    pass


def make_test_case(test_name):
    in_file = test_cases / f'{test_name}.py'
    golden_file = test_cases / f'{test_name}.py.golden'
    assert in_file.exists()
    assert golden_file.exists()

    def test(self: TestEndToEnd):
        code = in_file.read_text()
        res = make_tutor_spec_py(code)
        golden_res = json.loads(golden_file.read_text())
        self.assertEqual(res, golden_res)

    return test


# make all test cases dynamically!
for test_name in test_cases.iterdir():
    if test_name.suffix == '.py':
        test_case = make_test_case(test_name.stem)
        setattr(TestEndToEnd, f'test_{test_name.stem}', test_case)
