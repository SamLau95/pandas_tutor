"""
serializes run.py outputs into json.
"""

from __future__ import annotations

import types
from typing import Any, List, Tuple, TypeVar, Union

import pandas as pd

from pandas_tutor.parse_nodes import JoinCall, MergeCall, StartOfChain

from . import util
from .diagram import (
    DataPair,
    DataSpec,
    DataTwoLHS,
    DFSpec,
    Diagram,
    ErrorOutput,
    Explanation,
    Group,
    GroupBySpec,
    GroupData,
    ImageSpec,
    Index,
    Mark,
    PrevRHS,
    RuntimeErrorInChain,
    RuntimeErrorInSetup,
    ScalarSpec,
    SeriesGroupBySpec,
    SeriesSpec,
    SyntaxErrorOutput,
    UnhandledData,
)
from .marks import make_marks
from .run import (
    EvalResult,
    ImageResult,
    RuntimeErrorResult,
    ScalarResult,
    SyntaxErrorResult,
)

T = TypeVar("T")


def serialize(results: List[EvalResult]) -> Explanation:
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

    # HACK: special case for single val, updating this depends on truncating logic
    # result = truncate_vals(None, result, None)[0]

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
) -> Union[Diagram, ErrorOutput]:
    if isinstance(after, RuntimeErrorResult):
        return RuntimeErrorInChain.from_runtime_error_result(after)
    step = after.step

    marks = make_marks(step, before, after)

    # before, after = truncate_vals(marks, before, after)

    lhs: Union[DataSpec, PrevRHS] = (
        serialize_step_val(before)
        if isinstance(before.step, StartOfChain)
        else "prev_rhs"
    )
    rhs = serialize_step_val(after)

    # HACK: special case for merge and join
    data: Union[DataTwoLHS, DataPair]
    if isinstance(step, (MergeCall, JoinCall)):
        lhs2 = (
            after.args["right"]
            if "right" in after.args
            else after.args["other"]
            if "other" in after.args
            else None
        )
        data = DataTwoLHS(
            lhs=lhs,
            lhs2=serialize_pd_val(lhs2),
            rhs=rhs,
        )
    else:
        data = DataPair(lhs=lhs, rhs=rhs)

    return Diagram(
        type=step.type_,
        code_step=step.code,
        fragment=after.fragment,
        marks=marks,
        data=data,
    )


def serialize_step_val(step: EvalResult) -> DataSpec:
    """
    if we have an EvalResult, use this for serializing so that we can handle
    special results like images
    """
    if isinstance(step, ImageResult):
        return serialize_image(step.val)
    if isinstance(step, ScalarResult):
        return serialize_scalar(step.val)
    return serialize_pd_val(step.val)


def serialize_pd_val(val: Any) -> DataSpec:
    # HACK: special case for babypandas: pull original pd object out. we need
    # this here and in run.py since this handles the merge case where there are
    # two lhs values
    val = util.get_pd_from_babypandas(val)

    if isinstance(val, pd.DataFrame):
        return DFSpec.from_pd(val)
    if isinstance(val, pd.Series):
        return SeriesSpec.from_pd(val)
    if isinstance(val, util.DataFrameGroupBy):
        return serialize_groupby(val)
    if isinstance(val, util.SeriesGroupBy):
        return serialize_seriesgroupby(val)

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
        data=util.df_data(df),
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
        data=util.series_data(series),
        group_data=group_data,
    )


def serialize_image(val: Any) -> ImageSpec:
    return ImageSpec(util.base64_encode_plot(val))


def serialize_scalar(val: Any) -> ScalarSpec:
    py_type = str(type(val))
    # use str() on value so that the frontend can just display it
    data = str(util.json_scalar(val))
    return ScalarSpec(py_type=py_type, data=data)


def pairs(seq: List[T]) -> List[Tuple[T, T]]:
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]


def truncate_vals(
    mark: List[Mark], before: EvalResult, after: EvalResult
) -> Tuple[EvalResult, EvalResult]:
    """
    when we have really big dataframes / series, we'll trim out rows to avoid
    slowing down user's browsers.

    NOTE: this method mutates (!) the `before` and `after` objects.
    """

    if before is not None:
        before.val = top_bottom(before.val)
    if after is not None:
        after.val = top_bottom(after.val)
    return before, after


def top_bottom(val: Any, max_rows: int = 50) -> Any:
    """
    The only function used to truncate really big dataframe / series for NOW.
    Regardless of the operations, the function will ALWAYS, in default,
    truncate the first 25 and last 25 rows and columns of a dataframes / series

    NOTE: This method is temporary as we implement more sophisticated
    functions that truncate the dataframes / series using the markdown
    generated by the before and after eval results.
    """
    head_tail = max_rows // 2
    if isinstance(val, (pd.DataFrame, pd.Series)):
        val = (
            pd.concat([val.head(head_tail), val.tail(head_tail)])
            if len(val) > max_rows
            else val
        )
        val = (
            pd.concat(
                [val.iloc[:, :head_tail], val.iloc[:, -head_tail:]], axis=1
            )
            if isinstance(val, pd.DataFrame) and len(val.columns) > max_rows
            else val
        )
    elif isinstance(val, pd.Index):
        val = (
            pd.Index(val[:head_tail].tolist() + val[-head_tail:].tolist())
            if len(val) > max_rows
            else val
        )
    elif isinstance(val, util.DataFrameGroupBy):
        # groupby objects contain lots of data across many attributes,
        # so we need to recreate the object after pruning it
        temp_df = top_bottom(val.obj, max_rows)

        # dogs.groupby("size")[["breed", "price"]]
        # groupby after slicing for df isn't stored in groupby.obj, only stored in groupby._selection
        if isinstance(val._selection, list):
            temp_df = temp_df[val._selection]

        val = temp_df.groupby(val.grouper)
    elif isinstance(val, util.SeriesGroupBy):
        val.obj = top_bottom(val.obj, max_rows)

    return val
