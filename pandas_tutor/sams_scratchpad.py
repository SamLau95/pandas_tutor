'''
just for myself
'''
# flake8: noqa

import prettyprinter  # type: ignore
from prettyprinter import cpprint  # type: ignore
from prettyprinter.prettyprinter import IMPLICIT_MODULES  # type: ignore

from .parse import parse
from .run import run
from .main import make_tutor_spec_py

prettyprinter.install_extras(include=['dataclasses', 'python', 'numpy'])

# https://github.com/tommikaikkonen/prettyprinter/issues/27#issuecomment-451515061
IMPLICIT_MODULES.add('pandas_tutor.parse_nodes')

shorten_df = True

file_to_read = 'parse_golden/loc_one_val_01'


def p(obj):
    cpprint(obj, indent=2, ribbon_width=80)


if __name__ == "__main__":
    from pathlib import Path
    code = (Path(__file__).parent / f'tests/{file_to_read}.py').read_text()
    root = parse(code)
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

    print('\n---------------------------------------------------------\n')
