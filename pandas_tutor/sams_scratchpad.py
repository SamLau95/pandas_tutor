"""
just for myself
"""
# type: ignore
# flake8: noqa

import prettyprinter  # type: ignore
from prettyprinter import cpprint  # type: ignore
from prettyprinter.prettyprinter import IMPLICIT_MODULES
import simplejson as json
from pandas_tutor.diagram import encode_dataclasses

from pandas_tutor.parse_nodes import Call, SortValuesCall  # type: ignore

from .parse import parse, test_logger, test_parser
from .run import run
from .__main__ import make_tutor_spec, make_tutor_spec_py

prettyprinter.install_extras(include=["dataclasses", "python", "numpy"])

# https://github.com/tommikaikkonen/prettyprinter/issues/27#issuecomment-451515061
IMPLICIT_MODULES.add("pandas_tutor.parse_nodes")
IMPLICIT_MODULES.add("pandas_tutor.util")

shorten_df = True

file_to_read = "parse_golden/assignment_last_line_01"


def p(obj):
    cpprint(obj, indent=2, ribbon_width=80)


if __name__ == "__main__":
    from pathlib import Path

    code = (Path(__file__).parent / f"tests/{file_to_read}.py").read_text()
    root = test_parser(code)
    # test_logger(code)
    #     print(code)
    #     print('\n--------------\n')

    # if shorten_df:
    #     for diagram in spec:
    #         lhs = diagram['data_frame']['lhs']
    #         rhs = diagram['data_frame']['rhs']
    #         lhs['data'] = len(lhs['data'])
    #         rhs['data'] = len(rhs['data'])

    p(root)
    # p(run(root))
    # spec = make_tutor_spec(code)
    # p(spec)

    print("\n---------------------------------------------------------\n")
