'''
serializes run.py outputs into json.
'''

from __future__ import annotations

import typing as t

import pandas as pd  # type: ignore

from .diagram import DFPair, DFSpec, Diagram
from .marks import make_marks
from .run import EvalResult

T = t.TypeVar('T')


def serialize(results: t.List[EvalResult]) -> t.List[Diagram]:
    return [
        serialize_one_step(before, after) for before, after in pairs(results)
    ]


def serialize_to_json(results: t.List[EvalResult]) -> str:
    diagrams = serialize(results)
    return Diagram.to_json(diagrams)


def serialize_one_step(before: EvalResult, after: EvalResult) -> Diagram:
    step = after.step

    marks = make_marks(step, before, after)

    df_pair = DFPair(
        lhs=make_df_spec(before.df),
        rhs=make_df_spec(after.df),
    )

    return Diagram(type=step.type_,
                   code_step=step.code,
                   mapping=marks,
                   data_frame=df_pair)


def make_df_spec(df: pd.DataFrame):
    return DFSpec(col_names=df.columns.tolist(),
                  row_labels=df.index.tolist(),
                  data=df.to_numpy().tolist())  # type: ignore


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
