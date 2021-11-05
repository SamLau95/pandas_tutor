'''
just for myself
'''
# flake8: noqa

import prettyprinter  # type: ignore
from prettyprinter import cpprint as p  # type: ignore
from prettyprinter.prettyprinter import IMPLICIT_MODULES  # type: ignore

from pandas_tutor.parse import test_parser

from .main import make_tutor_spec_py

prettyprinter.install_extras(include=['dataclasses', 'python', 'numpy'])

# https://github.com/tommikaikkonen/prettyprinter/issues/27#issuecomment-451515061
IMPLICIT_MODULES.add('pandas_tutor.parse_nodes')

shorten_df = True

file_to_read = 'parse_golden/sort_value_args'

if __name__ == "__main__":
    from pathlib import Path
    code = (Path(__file__).parent / f'tests/{file_to_read}.py').read_text()
    spec = test_parser(code)
    #     print(code)
    #     print('\n--------------\n')

    # if shorten_df:
    #     for diagram in spec:
    #         lhs = diagram['data_frame']['lhs']
    #         rhs = diagram['data_frame']['rhs']
    #         lhs['data'] = len(lhs['data'])
    #         rhs['data'] = len(rhs['data'])
    p(spec, indent=2, ribbon_width=80)
    print('\n---------------------------------------------------------\n')
