from pathlib import Path
import unittest
import json

from ..parse import parse

golden = Path(__file__).parent / 'parse_golden'


class TestParse(unittest.TestCase):
    pass


def make_test_case(test_name):
    in_file = golden / f'{test_name}.py'
    golden_file = golden / f'{test_name}.py.golden'
    assert in_file.exists()
    assert golden_file.exists()

    def test(self):
        code = in_file.read_text()
        res = parse(code)
        golden_res = json.loads(golden_file.read_text())
        self.assertEqual(res, golden_res)

    return test


if __name__ == "__main__":
    for test_name in golden.iterdir():
        if test_name.suffix == '.py':
            test_case = make_test_case(test_name.stem)
            setattr(TestParse, f'test_{test_name.stem}', test_case)

    unittest.main()
