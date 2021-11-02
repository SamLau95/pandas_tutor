'''
just for myself
'''

from pprint import pprint

from .main import make_tutor_spec_py

shorten_df = True

file_to_read = 'sort_values_02'

if __name__ == "__main__":
    from pathlib import Path
    code = (Path(__file__).parent /
            f'tests/e2e_golden/{file_to_read}.py').read_text()
    spec = make_tutor_spec_py(code)
    #     print(code)
    #     print('\n--------------\n')

    if shorten_df:
        for diagram in spec:
            lhs = diagram['data_frame']['lhs']
            rhs = diagram['data_frame']['rhs']
            lhs['data'] = len(lhs['data'])
            rhs['data'] = len(rhs['data'])
    pprint(spec)
    print('\n---------------------------------------------------------\n')
