'''
executes parsed python code to compute the intermediate values within the
last line of the code.
'''

from __future__ import annotations

import builtins
import dataclasses
import pdb
import types
import typing as t

import pandas as pd  # type: ignore

from .parse_nodes import ChainStatement, ChainStep, ParsedModule, RawCode, Subscript


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

    import pdb
    pdb.set_trace()

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


def eval_args(step: ChainStep, user_globals: dict) -> dict:
    '''eval each arg marked with parse_nodes.evals_into()'''
    if isinstance(step, Subscript):
        return eval_args_subscript(step, user_globals)
    return eval_dataclass(step, user_globals)


def eval_args_subscript(step: Subscript, user_globals: dict) -> dict:
    '''subscripts have nested eval exprs so we have a special case'''
    slice1_args = eval_dataclass(step.slice1, user_globals, attr='slice1')
    slice2_args = eval_dataclass(step.slice2, user_globals, attr='slice2')
    return {**slice1_args, **slice2_args}


def eval_dataclass(obj: t.Any, user_globals: dict, attr='') -> dict:
    '''
    takes a dataclasss with fields marked by evals_into(), outputs
    dict of evaluated values
    '''
    args = {}
    if obj is None:
        return args

    fields = [
        field for field in dataclasses.fields(obj)
        if field.metadata.get('evals_into', False)
    ]

    for field in fields:
        evals_into = field.metadata['evals_into'].format(attr=attr)
        to_eval: t.Union[RawCode, t.List[RawCode]] = getattr(obj, field.name)
        if isinstance(to_eval, list):
            result = [eval(f"({code})", user_globals) for code in to_eval]
        else:
            result = eval(f"({to_eval})", user_globals)
        args[evals_into] = result
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
