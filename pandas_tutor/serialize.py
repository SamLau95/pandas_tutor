'''
serializes run.py outputs into json.
'''

from __future__ import annotations

import typing as t

from . import util
from .diagram import (DataPair, DataSpec, DFSpec, Diagram, Group, GroupBySpec,
                      GroupData, SeriesGroupBySpec, SeriesSpec, UnhandledData)
from .marks import make_marks
from .run import (DFResult, EvalResult, GroupbyResult, SeriesGroupbyResult,
                  SeriesResult)

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
    df_pair = DataPair(
        lhs=serialize_step_val(before),
        rhs=serialize_step_val(after),
    )

    return Diagram(type=step.type_,
                   code_step=step.code,
                   mapping=marks,
                   data_frame=df_pair)


def serialize_step_val(step: EvalResult) -> DataSpec:
    if isinstance(step, DFResult):
        df = step.val
        return DFSpec(col_names=df.columns.tolist(),
                      row_labels=df.index.tolist(),
                      data=df.to_numpy().tolist())
    elif isinstance(step, SeriesResult):
        series = step.val
        return SeriesSpec(row_labels=series.index.tolist(),
                          data=series.tolist())
    elif isinstance(step, GroupbyResult):
        return serialize_groupby(step.val)
    elif isinstance(step, SeriesGroupbyResult):
        return serialize_seriesgroupby(step.val)
    else:
        val = step.val
        return UnhandledData(data=str(val))


def serialize_groupby(val: util.DataFrameGroupBy) -> GroupBySpec:
    col_names = util.grouping_labels(val)

    df_groups = t.cast(util.Groups, val.groups)
    groups = [
        Group(name=[name] if isinstance(name, str) else list(name),
              labels=labels.tolist()) for name, labels in df_groups.items()
    ]

    df = util.ungroup(val)

    group_data = GroupData(col_names=col_names, groups=groups)
    return GroupBySpec(
        col_names=df.columns.tolist(),
        row_labels=df.index.tolist(),
        data=df.to_numpy().tolist(),  # type: ignore
        group_data=group_data)


def serialize_seriesgroupby(val: util.SeriesGroupBy) -> SeriesGroupBySpec:
    col_names = util.grouping_labels(val)

    df_groups = t.cast(util.Groups, val.groups)
    groups = [
        Group(name=[name] if isinstance(name, str) else list(name),
              labels=labels.tolist()) for name, labels in df_groups.items()
    ]

    series = util.ungroup(val)
    group_data = GroupData(col_names=col_names, groups=groups)
    return SeriesGroupBySpec(
        row_labels=series.index.tolist(),
        data=series.tolist(),  # type: ignore
        group_data=group_data)


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
