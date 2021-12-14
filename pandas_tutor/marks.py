'''
creates mark specs. here's where the magic happens!
'''
import typing as t

import pandas as pd

from . import util
from .diagram import CrossOut, Highlight, Mark, Outline, Selection, TablePos
from .parse_nodes import (AggCall, ApplyCall, AssignCall, Axis, ChainStep,
                          DropCall, EvalError, GroupByCall, HeadCall,
                          PassThroughCall, RenameCall, SortValuesCall,
                          SubsComparison, Subscript, SubscriptEl, TailCall)
from .run import (Arg, DFResult, EvalResult, GroupbyResult,
                  SeriesGroupbyResult, SeriesResult)


# step comes from after.step, but we pull it out here to help with
# the type checker
def make_marks(step: ChainStep, before: EvalResult,
               after: EvalResult) -> t.List[Mark]:
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
    elif isinstance(step, Subscript):
        return mark_for_subscript(step, before, after)
    else:
        return no_marks()


# df.sort_values('Name')
def mark_for_sort_values(step: SortValuesCall, before: EvalResult,
                         after: EvalResult) -> t.List[Mark]:
    if not (isinstance(before, (DFResult, SeriesResult))
            and isinstance(after, (DFResult, SeriesResult))):
        return []
    df = before.val
    args = after.args

    sort_by = args.get('labels', [])
    if isinstance(sort_by, str):
        sort_by = [sort_by]

    sorted_labels = df.index if step.axis == 'index' else df.columns

    # highlight sorted cols in RHS since the LHS values aren't sorted
    highlights = make_highlights(sort_by,
                                 selection(step.axis, other=True),
                                 anchor='rhs')
    outlines = make_outlines(sorted_labels, selection(step.axis))
    return [*highlights, *outlines]


# dogs.drop(columns=['type', 'price'])
def mark_for_drop(step: DropCall, before: EvalResult,
                  after: EvalResult) -> t.List[Mark]:
    if not (isinstance(before, (DFResult, SeriesResult))
            and isinstance(after, (DFResult, SeriesResult))):
        return []
    args = after.args

    col_labels = args.get('col_labels', [])
    if not util.is_list_like(col_labels):
        col_labels = [col_labels]

    row_labels = args.get('row_labels', [])
    if not util.is_list_like(row_labels):
        row_labels = [row_labels]

    # cross out dropped rows or columns
    return [
        *make_crossouts(col_labels, 'column'),
        *make_crossouts(row_labels, 'row')
    ]


# df.rename(index={'sam': 'smae'})
def mark_for_rename(step: RenameCall, before: EvalResult,
                    after: EvalResult) -> t.List[Mark]:
    args = after.args
    mapping: t.Any = args.get('mapping', {})

    if not isinstance(mapping, dict):
        return no_marks()

    select = selection(step.axis)

    return [
        Outline(select=select, from_=lhs(old), to=rhs(new))
        for old, new in mapping.items()
    ]


# df.head(2)
# df.tail()
def mark_for_head_or_tail(step: t.Union[HeadCall,
                                        TailCall], before: EvalResult,
                          after: EvalResult) -> t.List[Mark]:
    if not (isinstance(before, (DFResult, SeriesResult))
            and isinstance(after, (DFResult, SeriesResult))):
        return []
    return diff_rows(before.val, after.val)


# df['breed'].apply(len)
def mark_for_apply(step: ApplyCall, before: EvalResult,
                   after: EvalResult) -> t.List[Mark]:
    if isinstance(before, DFResult) and isinstance(after, DFResult):
        df = after.val
        labels = df.index if step.axis == 'index' else df.columns
        return make_outlines(labels, selection(step.axis))
    elif isinstance(before, DFResult) and isinstance(after, SeriesResult):
        # dogs.apply(len)  -> series with column names as index
        # special case: result is transposed! but i think this is confusing to
        # draw arrows for (since we draw arrows from column to rows) so let's
        # not bother with this.
        return []
    elif isinstance(before, SeriesResult) and isinstance(after, SeriesResult):
        labels = after.val.index
        return make_outlines(labels, 'row')
    else:
        # TODO: handle apply on groupby objects
        return []


# don't do anything super crazy for assigns...just highlight the new columns
# dogs.assign(daily=lambda df: df['food_cost'] * 30)
def mark_for_assign(step: AssignCall, before: EvalResult,
                    after: EvalResult) -> t.List[Mark]:
    return make_highlights(step.new_col_labels, 'column', 'rhs')


# df.groupby('hello')
def mark_for_groupby(step: GroupByCall, before: EvalResult,
                     after: EvalResult) -> t.List[Mark]:
    if not isinstance(after, GroupbyResult):
        return []

    group_cols = util.grouping_labels(after.val)
    highlights = make_highlights(group_cols,
                                 selection(step.axis, other=True),
                                 anchor='lhs')

    return highlights


# basic heuristic: assume that group keys map to row labels of result
def mark_for_agg(step: AggCall, before: EvalResult,
                 after: EvalResult) -> t.List[Mark]:
    if not isinstance(before, (GroupbyResult, SeriesGroupbyResult)):
        return []
    if not isinstance(after, (DFResult, SeriesResult)):
        return []

    groups = util.get_groups(before.val)

    row_outlines: t.List[Mark] = []
    for group_key, lhs_labels in groups.items():
        # don't draw anything if we have a multi-column group
        # TODO: support multi-column grouping
        if isinstance(group_key, tuple):
            continue

        for label in lhs_labels:
            row_outlines.append(
                Outline(
                    select='row',  # TODO: get selection from groupby
                    from_=lhs(label),
                    to=rhs(group_key),
                ))

    return row_outlines


# handler for all subscripts, like:
#
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
# df.groupby('Sex')[['Count']]
def mark_for_subscript(step: Subscript, before: EvalResult,
                       after: EvalResult) -> t.List[Mark]:
    if (isinstance(before, (DFResult, GroupbyResult))
            and isinstance(after, (SeriesResult, SeriesGroupbyResult))):
        return mark_for_subscript_into_series(step, before, after)
    elif isinstance(before, SeriesResult) and isinstance(after, SeriesResult):
        return mark_for_subscript_of_series(step, before, after)
    elif (isinstance(before, (DFResult, GroupbyResult))
          and isinstance(after, (DFResult, GroupbyResult))):
        return mark_for_subscript_df_to_df(step, before, after)
    else:
        return []


def mark_for_subscript_df_to_df(
    step: Subscript,
    before: t.Union[DFResult, GroupbyResult],
    after: t.Union[DFResult, GroupbyResult],
) -> t.List[Mark]:
    row_slice = step.slice1
    col_slice = step.slice2
    args = after.args

    before_df = util.ungroup(before.val)
    after_df = util.ungroup(after.val)

    # df.loc[:, df.iloc[0] % 2 == 0]
    rows_for_filter = make_subscript_comparison_marks(
        col_slice, args.get('slice2_filter_labels', []), 'row')

    no_filter_rows = len(rows_for_filter) == 0

    # df[df['Count'] > 14000]
    cols_for_filter = make_subscript_comparison_marks(
        row_slice, args.get('slice1_filter_labels', []), 'column')

    no_filter_cols = len(cols_for_filter) == 0

    return [
        *cols_for_filter,
        # if we're filtering, always display arrows between matching rows/cols
        *diff_cols(before_df, after_df, only_if_diff=no_filter_rows),
        *rows_for_filter,
        *diff_rows(before_df, after_df, only_if_diff=no_filter_cols),
    ]


def make_subscript_comparison_marks(
    subs_el: t.Optional[SubscriptEl],
    labels: Arg,
    selection: Selection,
) -> t.List[Mark]:
    '''
    makes highlights for cols/rows used for filtering, if the subscript is a
    filter.
    '''
    return (make_highlights(labels, selection) if isinstance(
        subs_el, SubsComparison) else [])


def mark_for_subscript_of_series(
    step: Subscript,
    before: SeriesResult,
    after: SeriesResult,
) -> t.List[Mark]:
    # no special cases for comparisons since there isn't a "column" we're using
    # to filter
    return diff_rows(before.val, after.val)


def mark_for_subscript_into_series(
    step: Subscript,
    before: t.Union[DFResult, GroupbyResult],
    after: t.Union[SeriesResult, SeriesGroupbyResult],
) -> t.List[Mark]:
    args = after.args
    before_df = util.ungroup(before.val)
    after_df = util.ungroup(after.val)

    # df['kids']
    if step.slicer is None:
        maybe_col = args.get('slice1_values')
        if not isinstance(maybe_col, (str, int)):
            return []

        return [
            Outline(select='column', from_=lhs(maybe_col), to=rhs_series())
        ]

    # df.loc[df["email"] > "s", "web"]
    # df.loc[:, df.iloc[0] % 2 == 0]
    row_slice = step.slice1
    col_slice = step.slice2

    # df.loc['sam@sam.com', df.loc['jan@jan.com'] > 10]
    rows_used_for_filter = make_subscript_comparison_marks(
        col_slice, args.get('slice2_filter_labels', []), 'row')

    # df.loc[df['Count'] > 14000, 'Name']
    cols_used_for_filter = make_subscript_comparison_marks(
        row_slice, args.get('slice1_filter_labels', []), 'column')

    maybe_row = args.get('slice1_values')
    # TODO: indexers can be more types than just str and int e.g. datetimes
    if isinstance(maybe_row, (str, int)):
        row = util.positions_to_labels(
            maybe_row,
            df=before_df,
            slicer=step.slicer,
            axis='index',
        )

        return [
            *rows_used_for_filter,
            Outline(select='row', from_=lhs(row), to=rhs_series()),
            # when slicing a row out of dataframe, the resulting series has
            # the df's column labels as the index. this means that the labels
            # are "transposed" so we don't draw arrows for this case.
        ]

    # df.iloc[:, 0]
    maybe_col = args.get('slice2_values')
    if isinstance(maybe_col, (str, int)):
        col = util.positions_to_labels(
            maybe_col,
            df=before_df,
            slicer=step.slicer,
            axis='columns',
        )
        return [
            *cols_used_for_filter,
            Outline(select='column', from_=lhs(col), to=rhs_series()),
            *diff_rows(before_df,
                       after_df,
                       only_if_diff=(len(cols_used_for_filter) == 0)),
        ]

    return []


def diff_dfs(df1: pd.DataFrame, df2: pd.DataFrame):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    / col
    '''
    rows = diff_rows(df1, df2)
    cols = diff_cols(df1, df2)
    return [*cols, *rows]


def diff_rows(df1: util.HasIndex, df2: util.HasIndex, only_if_diff=True):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights.
    '''
    row_matches = util.match_rows(df1, df2, only_if_diff)
    return make_outlines(row_matches, 'row')


def diff_cols(df1: pd.DataFrame, df2: pd.DataFrame, only_if_diff=True):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights.
    '''
    col_matches = util.match_cols(df1, df2, only_if_diff)
    return make_outlines(col_matches, 'column')


def no_marks(*args) -> t.List[Mark]:
    # print(f'Unknown mark for {step.type_}')
    return []


def selection(axis: Axis, other=False) -> Selection:
    if other:
        return 'column' if axis == 'index' else 'row'
    return 'row' if axis == 'index' else 'column'


def make_highlights(labels: t.Iterable,
                    select: Selection,
                    anchor='lhs') -> t.List[Mark]:
    '''
    shorthand to make a highlight for each label
    '''
    return [
        Highlight(label=label, select=select, anchor=anchor)
        for label in labels
    ]


def make_outlines(labels: t.Iterable, select: Selection) -> t.List[Mark]:
    '''
    shorthand when index values don't change, which is most of the time
    '''
    return [
        Outline(select=select, from_=lhs(label), to=rhs(label))
        for label in labels
    ]


def make_crossouts(labels: t.Iterable, select: Selection) -> t.List[Mark]:
    '''
    shorthand for crossouts
    '''
    # we haven't implemented arg anchors yet, so use a dummy value for now
    dummy_arg_anchor = {'anchor': 'arg', 'index': 0}
    return [
        CrossOut(
            select=select,
            from_=dummy_arg_anchor,  # type: ignore
            to=lhs(label),
        ) for label in labels
    ]


def lhs(label):
    return TablePos('lhs', label)


def rhs(label):
    return TablePos('rhs', label)


def lhs_series():
    return lhs('pandas.Series')


def rhs_series():
    return rhs('pandas.Series')
