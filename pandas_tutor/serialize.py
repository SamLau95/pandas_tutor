"""
serializes run.py outputs into json.
"""

from __future__ import annotations

import types
import typing as t

from pandas_tutor.parse_nodes import StartOfChain

from . import util
from .diagram import (
    DataPair,
    DataSpec,
    DFSpec,
    Diagram,
    ErrorOutput,
    Explanation,
    Group,
    GroupBySpec,
    GroupData,
    ImageSpec,
    Index,
    RuntimeErrorInChain,
    RuntimeErrorInSetup,
    SeriesGroupBySpec,
    SeriesSpec,
    SyntaxErrorOutput,
    UnhandledData,
)
from .marks import make_marks
from .run import (
    DFResult,
    EvalResult,
    GroupbyResult,
    ImageResult,
    RuntimeErrorResult,
    SeriesGroupbyResult,
    SeriesResult,
    SyntaxErrorResult,
)

T = t.TypeVar("T")


def serialize(results: t.List[EvalResult]) -> Explanation:
    if len(results) == 0:
        return []

    # stop if results use too much memory
    total_mem_used = sum(util.mem_used(result.val) for result in results)
    if total_mem_used > util.MEM_LIMIT:
        result = results[-1]
        return [
            RuntimeErrorInChain(
                code_step=result.step.code,
                message=util.too_much_mem_msg(total_mem_used),
                fragment=result.fragment,
            )
        ]

    if len(results) == 1:
        # happens when user inputs `df` without a function call, or when
        # error happens in setup code
        return serialize_single(results[0])

    return [serialize_pair(before, after) for before, after in pairs(results)]


def serialize_single(result: EvalResult) -> Explanation:
    if isinstance(result, SyntaxErrorResult):
        return [SyntaxErrorOutput.from_parse_syntax_error(result.step)]
    elif isinstance(result, RuntimeErrorResult):
        return [RuntimeErrorInSetup.from_runtime_error_result(result)]
    return [
        Diagram(
            type=result.step.type_,
            code_step=result.step.code,
            fragment=result.fragment,
            marks=[],
            data=DataPair(lhs=serialize_step_val(result), rhs="no_rhs"),
        )
    ]


def serialize_pair(
    before: EvalResult, after: EvalResult
) -> t.Union[Diagram, ErrorOutput]:
    if isinstance(after, RuntimeErrorResult):
        return RuntimeErrorInChain.from_runtime_error_result(after)
    step = after.step

    marks = make_marks(step, before, after)

    # this serializes every df twice when we should only do it once.
    # TODO: optimize this
    df_pair = DataPair(
        lhs=(
            serialize_step_val(before)
            if isinstance(before.step, StartOfChain)
            else "prev_rhs"
        ),
        rhs=serialize_step_val(after),
    )

    return Diagram(
        type=step.type_,
        code_step=step.code,
        fragment=after.fragment,
        marks=marks,
        data=df_pair,
    )


def serialize_step_val(step: EvalResult) -> DataSpec:
    if isinstance(step, DFResult):
        df = step.val
        return DFSpec(
            columns=Index.from_pd(df.columns),
            index=Index.from_pd(df.index),
            data=util.prep_df_data(df),
        )
    elif isinstance(step, SeriesResult):
        series = step.val
        return SeriesSpec(
            index=Index.from_pd(series.index),
            data=util.prep_series_data(series),
        )
    elif isinstance(step, GroupbyResult):
        return serialize_groupby(step.val)
    elif isinstance(step, SeriesGroupbyResult):
        return serialize_seriesgroupby(step.val)
    elif isinstance(step, ImageResult):
        return serialize_image(step.val)
    else:
        val = step.val
        if isinstance(val, types.ModuleType):
            # take off module path from the module output, otherwise tests
            # don't work in CI
            data = f"<module '{val.__name__}'>"
        else:
            data = repr(val)
        return UnhandledData(data=data)


def serialize_groupby(val: util.DataFrameGroupBy) -> GroupBySpec:
    col_names = util.grouping_labels(val)

    df_groups = util.get_groups(val)
    groups = [
        Group(
            name=list(name) if util.is_list_like(name) else [name],
            labels=labels.tolist(),
        )
        for name, labels in df_groups.items()
    ]

    df = util.ungroup(val)
    group_data = GroupData(columns=col_names, groups=groups)
    return GroupBySpec(
        columns=Index.from_pd(df.columns),
        index=Index.from_pd(df.index),
        data=util.prep_df_data(df),
        group_data=group_data,
    )


def serialize_seriesgroupby(val: util.SeriesGroupBy) -> SeriesGroupBySpec:
    col_names = util.grouping_labels(val)

    df_groups = util.get_groups(val)
    groups = [
        Group(
            name=list(name) if util.is_list_like(name) else [name],
            labels=labels.tolist(),
        )
        for name, labels in df_groups.items()
    ]

    series = util.ungroup(val)
    group_data = GroupData(columns=col_names, groups=groups)
    return SeriesGroupBySpec(
        index=Index.from_pd(series.index),
        data=util.prep_series_data(series),
        group_data=group_data,
    )


def serialize_image(val: t.Any) -> ImageSpec:
    return ImageSpec(util.base64_encode_plot(val))


def pairs(seq: t.List[T]) -> t.List[t.Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
