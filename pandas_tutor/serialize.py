'''
serializes run.py outputs into json.
'''

from __future__ import annotations

import typing as t

import numpy as np
import pandas as pd  # type: ignore

from .diagram import DFPair, DFSpec, Diagram
from .marks import make_marks
from .run import DFResult, EvalResult, GroupbyResult
from . import util

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

    # this serializes every df twice when we should only do it once.
    # TODO: optimize this
    df_pair = DFPair(
        lhs=serialize_step_val(before),
        rhs=serialize_step_val(after),
    )

    return Diagram(type=step.type_,
                   code_step=step.code,
                   mapping=marks,
                   data_frame=df_pair)


def serialize_step_val(step: EvalResult) -> DFSpec:
    df: pd.DataFrame
    if isinstance(step, DFResult):
        df = step.val
    elif isinstance(step, GroupbyResult):
        return serialize_groupby(step.val)
    else:
        # step.val is unhandled, so we'll do some heuristics
        val = step.val
        if isinstance(val, str):
            df = pd.DataFrame([val], columns=['value'])
        elif isinstance(val, pd.Series):
            df = val.to_frame()
        elif isinstance(val, list) or isinstance(val, np.ndarray):
            df = pd.DataFrame(val, columns=['value'])
        elif isinstance(val, dict):
            df = pd.DataFrame(val)
        else:
            # fallback: cast to string
            df = pd.DataFrame(str(val), columns=['value'])

    return DFSpec(col_names=df.columns.tolist(),
                  row_labels=df.index.tolist(),
                  data=df.to_numpy().tolist())  # type: ignore


def serialize_groupby(val: util.DataFrameGroupBy) -> DFSpec:
    # val.groups is {group: labels}, but group can be a tuple (when grouping on
    # multiple cols), and labels is a pandas index
    groups = {
        str(k): v.tolist()  # type: ignore
        for k, v in val.groups.items()
    }
    df = util.ungroup(val)
    return DFSpec(
        col_names=df.columns.tolist(),
        row_labels=df.index.tolist(),
        data=df.to_numpy().tolist(),  # type: ignore
        groups=groups)


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
