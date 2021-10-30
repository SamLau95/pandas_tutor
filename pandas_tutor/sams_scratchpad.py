'''
just for myself
'''

from .main import make_tutor_spec

file_to_read = 'sort_values_02'

if __name__ == "__main__":
    from pathlib import Path
    code = (Path(__file__).parent /
            f'tests/e2e_golden/{file_to_read}.py').read_text()
    spec = make_tutor_spec(code)
    #     print(code)
    #     print('\n--------------\n')
    print(spec)
