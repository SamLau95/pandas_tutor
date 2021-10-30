'''
serializes run.py outputs into json. here's where the magic happens!
'''

from __future__ import annotations

import dataclasses
import json
import typing as t

import pandas as pd  # type: ignore

from .diagram import DF, DFPair, Diagram
from .run import EvalResult

T = t.TypeVar('T')


class Encoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def serialize(results: t.List[EvalResult]) -> t.List[Diagram]:
    return [
        serialize_one_step(before, after) for before, after in pairs(results)
    ]


def serialize_to_json(results: t.List[EvalResult]) -> str:
    diagrams = serialize(results)
    return json.dumps(diagrams, indent=2, cls=Encoder)


def serialize_one_step(before: EvalResult, after: EvalResult) -> Diagram:
    step = after.step
    assert step.name is not None

    df_pair = DFPair(
        lhs=make_DF(before.df),
        rhs=make_DF(after.df),
    )

    return Diagram(type=step.name,
                   code_step=step.code,
                   mapping=[],
                   data_frame=df_pair)


def make_DF(df: pd.DataFrame):
    return DF(col_names=list(df.columns), data=df.to_dict(orient='records'))


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
