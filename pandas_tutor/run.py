'''
executes parsed python code to compute the intermediate values within the
last line of the code.
'''

from __future__ import annotations
import typing as t
import dataclasses

import pandas as pd  # type: ignore

from .parse import Node


@dataclasses.dataclass
class EvalResult:
    node: Node
    df: pd.DataFrame


def run(root: Node) -> t.List[EvalResult]:
    expressions = root.children

    # hard-code the last expression!
    setup_exprs, last_expr = expressions[:-1], expressions[-1]

    # all the code above the last expression
    setup_code = '\n'.join([expr.code for expr in setup_exprs])

    # now let's run stuff VERY VERY dangerously!
    exec(setup_code, globals())

    # wrap individual steps in parens before eval since they can have newlines
    eval_results = [
        EvalResult(node=node, df=eval(f"({node.code})", globals()))
        for node in last_expr.children
    ]

    return eval_results


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
