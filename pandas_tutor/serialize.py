'''
serializes run.py outputs into json. here's where the magic happens!
'''

from __future__ import annotations

import dataclasses
import json
import typing as t

import numpy as np
import pandas as pd  # type: ignore

from .diagram import DFPair, DFSpec, Diagram
from .marks import make_marks
from .run import EvalResult

T = t.TypeVar('T')


class DiagramEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            res = dataclasses.asdict(obj)

            # little hack to get from keys in JSON
            if 'from_' in res:
                res['from'] = res['from_']
                del res['from_']

            return res

        # extras for np objects
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def serialize(results: t.List[EvalResult]) -> t.List[Diagram]:
    return [
        serialize_one_step(before, after) for before, after in pairs(results)
    ]


def serialize_to_json(results: t.List[EvalResult]) -> str:
    diagrams = serialize(results)
    return json.dumps(diagrams, indent=2, cls=DiagramEncoder)


def serialize_one_step(before: EvalResult, after: EvalResult) -> Diagram:
    node = after.node
    assert node.name is not None

    marks = make_marks(node.name, before, after)

    df_pair = DFPair(
        lhs=make_df_spec(before.df),
        rhs=make_df_spec(after.df),
    )

    return Diagram(type=node.name,
                   code_step=node.code,
                   mapping=marks,
                   data_frame=df_pair)


def make_df_spec(df: pd.DataFrame):
    return DFSpec(col_names=list(df.columns),
                  data=df.to_dict(orient='records'))


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
