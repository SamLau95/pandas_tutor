'''
executes parsed python code to compute the intermediate values within the
last line of the code.
'''

from __future__ import annotations

import builtins
import dataclasses
import types
import typing as t

import pandas as pd  # type: ignore

from .parse_nodes import ChainStatement, ChainStep, ParsedModule


@dataclasses.dataclass
class EvalResult:
    step: ChainStep
    df: pd.DataFrame
    args: dict


# TODO: handle stdout and stderr from user code
def run(root: ParsedModule) -> t.List[EvalResult]:
    statements = root.statements

    # hard-code the last one!
    setup_stmts, last_expr = statements[:-1], statements[-1]
    assert isinstance(last_expr, ChainStatement)

    # all the code above the last expression
    setup_code = '\n'.join([stmt.code for stmt in setup_stmts])

    # now let's run stuff dangerously!
    user_globals = setup_user_globals()
    exec(setup_code, user_globals)

    # wrap individual steps in parens before eval since they can have newlines
    eval_results = [
        EvalResult(step=step,
                   df=eval(f"({step.code})", user_globals),
                   args=eval_args(step, user_globals))
        for step in last_expr.chain
    ]

    return eval_results


def setup_user_globals():
    # set up scope like PythonTutor
    user_builtins = {}
    assert isinstance(builtins, types.ModuleType)
    for k in dir(builtins):
        user_builtins[k] = getattr(builtins, k)

    user_globals = {}

    user_globals.update({
        "__name__": "__main__",
        "__builtins__": user_builtins
    })

    return user_globals


def eval_args(step: ChainStep, user_globals: dict):
    '''eval each arg marked with parse_nodes.evals_into()'''
    args = {}
    fields = dataclasses.fields(step)
    for field in fields:
        evals_into = field.metadata.get('evals_into', False)
        if evals_into:
            code_to_eval = getattr(step, field.name)
            args[evals_into] = eval(f"({code_to_eval})", user_globals)
    return args


test = '''
import pandas as pd

df = pd.DataFrame([('Liam', 'M', 19659, 2020), ('Noah', 'M', 18252, 2020),
                   ('Oliver', 'M', 14147, 2020), ('Elijah', 'M', 13034, 2020),
                   ('William', 'M', 12541, 2020), ('Emma', 'F', 15581, 2020),
                   ('Ava', 'F', 13084, 2020), ('Charlotte', 'F', 13003, 2020),
                   ('Sophia', 'F', 12976, 2020), ('Amelia', 'F', 12704, 2020)],
                  columns=['Name', 'Sex', 'Count', 'Year'])

(df
 .sort_values('Name')
)
'''.strip()

if __name__ == "__main__":
    from .parse import parse
    root = parse(test)
    res = run(root)

    for r in res:
        print(r)
