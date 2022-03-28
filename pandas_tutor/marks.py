"""
creates mark specs. here's where the magic happens!
"""
from collections.abc import Iterable
from typing import Any, List, Optional, Tuple, Union, cast
from collections.abc import Sequence

import pandas as pd

from . import util
from .diagram import (
    Anchor,
    AxisPos,
    CellPos,
    Drop,
    IndexLevel,
    IndexLevelPos,
    Map,
    Mark,
    Selection,
    SeriesPos,
    Using,
)
from .parse_nodes import (
    AggCall,
    ApplyCall,
    AssignCall,
    Axis,
    ChainStep,
    DropCall,
    EvalError,
    GroupByCall,
    HeadCall,
    PassThroughCall,
    PivotCall,
    RenameCall,
    ResetIndexCall,
    SortValuesCall,
    StackCall,
    SubsComparison,
    Subscript,
    SubscriptEl,
    TailCall,
    UnstackCall,
)
from .run import (
    Arg,
    DFResult,
    EvalResult,
    GroupbyResult,
    SeriesGroupbyResult,
    SeriesResult,
)


# step comes from after.step, but we pull it out here to help with
# the type checker.
def make_marks(
    step: ChainStep, before: EvalResult, after: EvalResult
) -> List[Mark]:
    """
    computes the marks for a given step by dispatching to the right marks
    function. returns empty list if we don't know how to make marks.
    """
    if isinstance(step, EvalError):
        return no_marks()
    elif isinstance(step, PassThroughCall):
        return no_marks()
    elif isinstance(step, SortValuesCall):
        return mark_for_sort_values(step, before, after)
    elif isinstance(step, DropCall):
        return mark_for_drop(step, before, after)
    elif isinstance(step, RenameCall):
        return mark_for_rename(step, before, after)
    elif isinstance(step, HeadCall) or isinstance(step, TailCall):
        return mark_for_head_or_tail(step, before, after)
    elif isinstance(step, ApplyCall):
        return mark_for_apply(step, before, after)
    elif isinstance(step, AssignCall):
        return mark_for_assign(step, before, after)
    elif isinstance(step, GroupByCall):
        return mark_for_groupby(step, before, after)
    elif isinstance(step, AggCall):
        return mark_for_agg(step, before, after)
    elif isinstance(step, ResetIndexCall):
        return mark_for_reset_index(step, before, after)
    elif isinstance(step, UnstackCall):
        return mark_for_unstack(step, before, after)
    elif isinstance(step, StackCall):
        return mark_for_stack(step, before, after)
    elif isinstance(step, PivotCall):
        return mark_for_pivot(step, before, after)
    elif isinstance(step, Subscript):
        return mark_for_subscript(step, before, after)
    else:
        return no_marks()


# df.sort_values('Name')
def mark_for_sort_values(
    step: SortValuesCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, (DFResult, SeriesResult))
    ):
        return []
    df = before.val
    args = after.args

    sort_by = args.get("labels", [])
    if isinstance(sort_by, str):
        sort_by = [sort_by]

    sorted_labels = df.index if step.axis == "index" else df.columns

    # highlight sorted cols in RHS since the LHS values aren't sorted
    highlights = make_highlights(
        sort_by, selection(step.axis, other=True), anchor="rhs"
    )
    outlines = make_outlines(sorted_labels, selection(step.axis))
    return [*highlights, *outlines]


# dogs.drop(columns=['type', 'price'])
def mark_for_drop(
    step: DropCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, (DFResult, SeriesResult))
    ):
        return []
    args = after.args

    col_labels = args.get("col_labels", [])
    if not util.is_list_like(col_labels):
        col_labels = [col_labels]

    row_labels = args.get("row_labels", [])
    if not util.is_list_like(row_labels):
        row_labels = [row_labels]

    # cross out dropped rows or columns
    return [
        *make_crossouts(col_labels, "column"),
        *make_crossouts(row_labels, "row"),
    ]


# df.rename(index={'sam': 'smae'})
def mark_for_rename(
    step: RenameCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    args = after.args
    mapping: Any = args.get("mapping", {})

    if not isinstance(mapping, dict):
        return no_marks()

    select = selection(step.axis)

    return [
        Map(from_=lhs(select, old), to=rhs(select, new))
        for old, new in mapping.items()
    ]


# df.head(2)
# df.tail()
def mark_for_head_or_tail(
    step: Union[HeadCall, TailCall], before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, (DFResult, SeriesResult))
    ):
        return []
    return diff_rows(before.val, after.val)


# df['breed'].apply(len)
def mark_for_apply(
    step: ApplyCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if isinstance(before, DFResult) and isinstance(after, DFResult):
        df = after.val
        labels = df.index if step.axis == "index" else df.columns
        return make_outlines(labels, selection(step.axis))
    elif isinstance(before, DFResult) and isinstance(after, SeriesResult):
        # dogs.apply(len)  -> series with column names as index
        # special case: result is transposed! but i think this is confusing to
        # draw arrows for (since we draw arrows from column to rows) so let's
        # not bother with this.
        return []
    elif isinstance(before, SeriesResult) and isinstance(after, SeriesResult):
        labels = after.val.index
        return make_outlines(labels, "row")
    else:
        # TODO: handle apply on groupby objects
        return []


# don't do anything super crazy for assigns...just highlight the new columns
# dogs.assign(daily=lambda df: df['food_cost'] * 30)
def mark_for_assign(
    step: AssignCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    return make_highlights(step.new_col_labels, "column", "rhs")


# df.groupby('hello')
def mark_for_groupby(
    step: GroupByCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not isinstance(after, GroupbyResult):
        return []

    group_cols = util.grouping_labels(after.val)
    highlights = make_highlights(
        group_cols, selection(step.axis, other=True), anchor="lhs"
    )

    return highlights


# basic heuristic: assume that group keys map to row labels of result
def mark_for_agg(
    step: AggCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not isinstance(before, (GroupbyResult, SeriesGroupbyResult)):
        return []
    if not isinstance(after, (DFResult, SeriesResult)):
        return []

    groups = util.get_groups(before.val)

    row_outlines: List[Mark] = []
    for group_key, lhs_labels in groups.items():
        for label in lhs_labels:
            row_outlines.append(
                # TODO: get selection from groupby instead of hard-coding 'row'
                Map(
                    from_=lhs("row", label),
                    to=rhs("row", group_key),
                )
            )

    return row_outlines


# dogs.reset_index(level=[1, 2], drop=True)
# i don't think this works properly when the column is a multi-index, but
# let's not worry about that for now
def mark_for_reset_index(
    step: ResetIndexCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, DFResult)
    ):
        return []
    df = before.val
    args = after.args

    # if level unspecified, pandas resets all levels
    all_levels = list(range(len(df.index.names)))
    levels = util.listify(args.get("level", all_levels))
    levels = [util.level_number(df.index, level) for level in levels]

    if args.get("drop", False):
        return [Drop(IndexLevelPos("lhs", "row", level)) for level in levels]

    # recreating the pandas defaults for unnamed index levels
    names: List[str]
    if util.is_multi(df.index):
        names = [
            name if name is not None else f"level_{position}"
            for position, name in enumerate(df.index.names)
        ]
    else:
        default = "index" if "index" not in df else "level_0"
        names = [default] if df.index.name is None else [df.index.name]

    return [
        Map(
            IndexLevelPos("lhs", "row", level),
            rhs("column", names[level]),
        )
        for level in levels
    ]


# counts.unstack(level=-1, fill_value=0)
def mark_for_unstack(
    step: UnstackCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, DFResult)
    ):
        return []

    df = before.val
    args = after.args

    # normally, pandas unstacks the index into the columns. but when there's
    # only one index level, pandas instead transposes the dataframe, then
    # *stacks* a level. it's a pretty strange edge case to draw arrows for, so
    # we don't handle it.
    if not util.is_multi(df.index):
        return []

    levels = util.listify(args.get("level", -1))
    levels = [util.level_number(df.index, level) for level in levels]

    columns = df.columns if util.is_dataframe(df) else pd.Index([util.SERIES])
    n_orig_levels = len(columns)

    index_marks: List[Mark] = [
        Map(
            lhs_index("row", level),
            # unstacking puts the new levels **under** the existing ones
            rhs_index("column", index_level + n_orig_levels),
        )
        for index_level, level in enumerate(levels)
    ]

    # for each cell: the unstacked labels move to the column index
    cells = util.push_levels(df.index, columns, levels)
    cell_marks: List[Mark] = [
        Map(CellPos("lhs", old_row, old_col), CellPos("rhs", new_row, new_col))
        for (old_row, old_col), (new_row, new_col) in cells
    ]

    return [*index_marks, *cell_marks]


# counts.stack(level=-1, drop_na=False)
def mark_for_stack(
    step: StackCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (
        isinstance(before, (DFResult))
        and isinstance(after, (DFResult, SeriesResult))
    ):
        return []

    df = before.val
    args = after.args

    levels = util.listify(args.get("level", len(df.columns.names) - 1))
    levels = [util.level_number(df.columns, level) for level in levels]

    # stacking puts the new levels **after** the existing ones
    n_index_levels = len(df.index.names)

    index_marks: List[Mark] = [
        Map(
            IndexLevelPos("lhs", "column", level),
            IndexLevelPos("rhs", "row", index_level + n_index_levels),
        )
        for index_level, level in enumerate(levels)
    ]

    # for each cell: the unstacked labels move to the row index
    is_series = isinstance(after, SeriesResult)
    cells = util.push_levels(df.columns, df.index, levels)
    cell_marks: List[Mark] = [
        Map(
            CellPos("lhs", old_row, old_col),
            CellPos("rhs", new_row, new_col if not is_series else util.SERIES),
        )
        for (old_col, old_row), (new_col, new_row) in cells
    ]

    return [*index_marks, *cell_marks]


# df.pivot(index='foo', columns='bar', values='baz')
def mark_for_pivot(
    step: PivotCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    # if index=[], pandas does the weird transpose + stack thing into a series
    # which we won't try to handle
    if not (isinstance(before, DFResult) and isinstance(after, DFResult)):
        return []

    df = before.val
    args = after.args

    has_index = "index" in args
    has_values = "values" in args
    index: List[util.Label] = util.listify(args.get("index", []))
    columns: List[util.Label] = util.listify(args.get("columns", []))
    # default values arg is all leftover columns
    values: List[util.Label] = util.listify(
        args.get("values", df.columns.drop([*index, *columns]))
    )
    no_value_cols = len(values) == 0

    # special case: when only one values column is specified, pandas
    # doesn't keep it as a column. we need has_values since pandas only drops
    # when values is explicitly passed in.
    will_drop_values = has_values and len(values) == 1
    n_orig_col_levels = len(df.columns.names) if not will_drop_values else 0

    # each index arg goes into a new index level
    index_marks = [
        Map(lhs("column", name), rhs_index("row", position))
        for position, name in enumerate(index)
    ]

    # special case: result is empty dataframe with new index
    if no_value_cols:
        return [*index_marks]

    # each column arg is appended as an index level into the columns
    column_marks = [
        Map(
            lhs("column", name),
            rhs_index("column", position + n_orig_col_levels),
        )
        for position, name in enumerate(columns)
    ]

    # to make cell marks, we need to pull row and column labels from the data
    # rows themselves so the logic is tricky
    cell_marks = []
    for old_row, row in df.iterrows():
        old_row = cast(util.Label, old_row)
        # pull new row labels from row data
        new_row = cast(util.Label, tuple(row[index]) if has_index else old_row)

        # pull new col labels from row data
        appended = tuple(row[columns])
        for old_col in values:
            new_col = (old_col, *appended) if not will_drop_values else appended
            left = CellPos("lhs", old_row, old_col)
            right = CellPos("rhs", new_row, new_col)
            cell_marks.append(Map(left, right))

    return [*index_marks, *column_marks, *cell_marks]


# handler for all subscripts, like:
#
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
# df.groupby('Sex')[['Count']]
def mark_for_subscript(
    step: Subscript, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if isinstance(before, (DFResult, GroupbyResult)) and isinstance(
        after, (SeriesResult, SeriesGroupbyResult)
    ):
        return mark_for_subscript_into_series(step, before, after)
    elif isinstance(before, SeriesResult) and isinstance(after, SeriesResult):
        return mark_for_subscript_of_series(step, before, after)
    elif isinstance(before, (DFResult, GroupbyResult)) and isinstance(
        after, (DFResult, GroupbyResult)
    ):
        return mark_for_subscript_df_to_df(step, before, after)
    else:
        return []


def mark_for_subscript_df_to_df(
    step: Subscript,
    before: Union[DFResult, GroupbyResult],
    after: Union[DFResult, GroupbyResult],
) -> List[Mark]:
    row_slice = step.slice1
    col_slice = step.slice2
    args = after.args

    before_df = util.ungroup(before.val)
    after_df = util.ungroup(after.val)

    # df.loc[:, df.iloc[0] % 2 == 0]
    rows_for_filter = make_subscript_comparison_marks(
        col_slice, args.get("slice2_filter_labels", []), "row"
    )

    no_filter_rows = len(rows_for_filter) == 0

    # df[df['Count'] > 14000]
    cols_for_filter = make_subscript_comparison_marks(
        row_slice, args.get("slice1_filter_labels", []), "column"
    )

    no_filter_cols = len(cols_for_filter) == 0

    return [
        *cols_for_filter,
        # if we're filtering, always display arrows between matching rows/cols
        *diff_cols(before_df, after_df, only_if_diff=no_filter_rows),
        *rows_for_filter,
        *diff_rows(before_df, after_df, only_if_diff=no_filter_cols),
    ]


def make_subscript_comparison_marks(
    subs_el: Optional[SubscriptEl],
    labels: Arg,
    selection: Selection,
) -> List[Mark]:
    """
    makes highlights for cols/rows used for filtering, if the subscript is a
    filter.
    """
    return (
        make_highlights(labels, selection)
        if isinstance(subs_el, SubsComparison)
        else []
    )


def mark_for_subscript_of_series(
    step: Subscript,
    before: SeriesResult,
    after: SeriesResult,
) -> List[Mark]:
    # no special cases for comparisons since there isn't a "column" we're using
    # to filter
    return diff_rows(before.val, after.val)


def mark_for_subscript_into_series(
    step: Subscript,
    before: Union[DFResult, GroupbyResult],
    after: Union[SeriesResult, SeriesGroupbyResult],
) -> List[Mark]:
    args = after.args
    before_df = util.ungroup(before.val)
    after_df = util.ungroup(after.val)

    # df['kids']
    if step.slicer is None:
        col = args.get("slice1_values")
        if not isinstance(col, (str, int)):
            return []

        return [Map(from_=lhs("column", col), to=rhs_series())]

    # df.loc[df["email"] > "s", "web"]
    # df.loc[:, df.iloc[0] % 2 == 0]
    row_slice = step.slice1
    col_slice = step.slice2

    # df.loc['sam@sam.com', df.loc['jan@jan.com'] > 10]
    rows_used_for_filter = make_subscript_comparison_marks(
        col_slice, args.get("slice2_filter_labels", []), "row"
    )

    # df.loc[df['Count'] > 14000, 'Name']
    cols_used_for_filter = make_subscript_comparison_marks(
        row_slice, args.get("slice1_filter_labels", []), "column"
    )

    maybe_row = args.get("slice1_values")
    # TODO: indexers can be more types than just str and int e.g. datetimes
    if isinstance(maybe_row, (str, int)):
        row = util.positions_to_labels(
            maybe_row,
            df=before_df,
            slicer=step.slicer,
            axis="index",
        )

        return [
            *rows_used_for_filter,
            Map(from_=lhs("row", row), to=rhs_series()),
            # when slicing a row out of dataframe, the resulting series has
            # the df's column labels as the index. this means that the labels
            # are "transposed" so we don't draw arrows for this case.
        ]

    # df.iloc[:, 0]
    col = args.get("slice2_values")
    if isinstance(col, (str, int)):
        label = util.positions_to_labels(
            col,
            df=before_df,
            slicer=step.slicer,
            axis="columns",
        )
        return [
            *cols_used_for_filter,
            Map(from_=lhs("column", label), to=rhs_series()),
            *diff_rows(
                before_df,
                after_df,
                only_if_diff=(len(cols_used_for_filter) == 0),
            ),
        ]

    return []


def diff_dfs(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    / col
    """
    rows = diff_rows(df1, df2)
    cols = diff_cols(df1, df2)
    return [*cols, *rows]


def diff_rows(df1: util.HasIndex, df2: util.HasIndex, only_if_diff=True):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights.
    """
    row_matches = util.match_rows(df1, df2, only_if_diff)
    return make_outlines(row_matches, "row")


def diff_cols(df1: pd.DataFrame, df2: pd.DataFrame, only_if_diff=True):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights.
    """
    col_matches = util.match_cols(df1, df2, only_if_diff)
    return make_outlines(col_matches, "column")


def no_marks(*args) -> List[Mark]:
    # print(f'Unknown mark for {step.type_}')
    return []


def selection(axis: Axis, other=False) -> Selection:
    if other:
        return "column" if axis == "index" else "row"
    return "row" if axis == "index" else "column"


def make_highlights(
    labels: Iterable, select: Selection, anchor: Anchor = "lhs"
) -> List[Mark]:
    """
    shorthand to make a highlight for each column/row in labels
    """
    return [Using(AxisPos(anchor, select, label)) for label in labels]


def make_outlines(labels: Iterable, select: Selection) -> List[Mark]:
    """
    shorthand when index values don't change, which is most of the time
    """
    return [
        Map(from_=lhs(select, label), to=rhs(select, label)) for label in labels
    ]


def make_crossouts(labels: Iterable, select: Selection) -> List[Mark]:
    """
    shorthand for crossouts
    """
    return [Drop(pos=lhs(select, label)) for label in labels]


def lhs(select: Selection, label: util.Label) -> AxisPos:
    """shorthand for a column/row in lhs"""
    return AxisPos("lhs", select, label)


def rhs(select: Selection, label: util.Label) -> AxisPos:
    """shorthand for a column/row in rhs"""
    return AxisPos("rhs", select, label)


def lhs_index(select: Selection, level: IndexLevel) -> IndexLevelPos:
    """shorthand for an index level in lhs"""
    return IndexLevelPos("lhs", select, level)


def rhs_index(select: Selection, level: IndexLevel) -> IndexLevelPos:
    """shorthand for an index level in rhs"""
    return IndexLevelPos("rhs", select, level)


def lhs_series() -> SeriesPos:
    """shorthand for the lhs series"""
    return SeriesPos("lhs")


def rhs_series() -> SeriesPos:
    """shorthand for the rhs series"""
    return SeriesPos("rhs")
