'''
creates mark specs. here's where the magic happens!
'''
import typing as t

import pandas as pd  # type: ignore

from . import util
from .diagram import Highlight, Mark, Outline, Selection, TablePos
from .parse_nodes import (AggCall, Axis, ChainStep, GroupByCall, HeadCall,
                          PassThroughCall, RenameCall, SortValuesCall,
                          SubsComparison, Subscript, TailCall)
from .run import DFResult, EvalResult, GroupbyResult, UnhandledResult


# step comes from after.step, but we pull it out here to help with
# the type checker
def make_marks(step: ChainStep, before: EvalResult,
               after: EvalResult) -> t.List[Mark]:
    if isinstance(step, SortValuesCall):
        return mark_for_sort_values(step, before, after)
    elif isinstance(step, RenameCall):
        return mark_for_rename(step, before, after)
    elif isinstance(step, HeadCall) or isinstance(step, TailCall):
        return mark_for_head_or_tail(step, before, after)
    elif isinstance(step, GroupByCall):
        return mark_for_groupby(step, before, after)
    elif isinstance(step, AggCall):
        return mark_for_agg(step, before, after)
    elif isinstance(step, PassThroughCall):
        return no_marks(step, before, after)
    elif isinstance(step, Subscript):
        return mark_for_subscript(step, before, after)
    else:
        return no_marks(step, before, after)


# df.sort_values('Name')
def mark_for_sort_values(step: SortValuesCall, before: EvalResult,
                         after: EvalResult) -> t.List[Mark]:
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
    if not (isinstance(before, DFResult) and isinstance(after, DFResult)):
        return []
    return diff_rows(before.val, after.val)


# df.groupby('hello')
def mark_for_groupby(step: GroupByCall, before: EvalResult,
                     after: EvalResult) -> t.List[Mark]:
    args = after.args

    group_cols = args.get('labels', [])
    # TODO: typeguard against function calls too
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    highlights = make_highlights(group_cols,
                                 selection(step.axis, other=True),
                                 anchor='lhs')

    return highlights


# df.head(2)
# df.tail()
# basic heuristic: assume that group keys map to row labels of result
def mark_for_agg(step: AggCall, before: EvalResult,
                 after: EvalResult) -> t.List[Mark]:
    if not isinstance(before, GroupbyResult):
        return []
    if not isinstance(after, DFResult):
        return []

    groups = t.cast(util.Groups, before.val.groups)

    row_outlines: t.List[Mark] = []
    for group_key, lhs_labels in groups.items():
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


# handles:
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
# df.groupby('Sex')[['Count']]
def mark_for_subscript(step: Subscript, before: EvalResult,
                       after: EvalResult) -> t.List[Mark]:
    before_df: pd.DataFrame
    after_df: pd.DataFrame

    if (isinstance(before, GroupbyResult)
            and isinstance(after, GroupbyResult)):
        before_df = util.ungroup(before.val)
        after_df = util.ungroup(after.val)
    elif not (isinstance(before, DFResult) and isinstance(after, DFResult)):
        return []
    else:
        before_df = before.val
        after_df = after.val

    row_slice = step.slice1
    col_slice = step.slice2
    args = after.args
    row_marks = diff_rows(before_df, after_df)
    col_marks = diff_cols(before_df, after_df)

    if isinstance(row_slice, SubsComparison):
        labels = args.get('slice1_labels', [])
        highlights = make_highlights(labels, 'column')
        col_marks = [*highlights, *col_marks]

    if isinstance(col_slice, SubsComparison):
        labels = args.get('slice2_labels', [])
        highlights = make_highlights(labels, 'row')
        row_marks = [*highlights, *row_marks]

    return [*col_marks, *row_marks]


def diff_dfs(df1: pd.DataFrame, df2: pd.DataFrame):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    / col
    '''
    rows = diff_rows(df1, df2)
    cols = diff_cols(df1, df2)
    return [*cols, *rows]


def diff_rows(df1: pd.DataFrame, df2: pd.DataFrame):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    '''
    row_matches = util.match_rows(df1, df2)
    return make_outlines(row_matches, 'row')


def diff_cols(df1: pd.DataFrame, df2: pd.DataFrame):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching col
    '''
    col_matches = util.match_cols(df1, df2)
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
    return [
        Highlight(label=label, select=select, anchor=anchor)
        for label in labels
    ]


def make_outlines(labels: t.Iterable, select: Selection) -> t.List[Mark]:
    '''
    used as a shorthand when index values don't change, which is most of the
    time
    '''
    return [
        Outline(select=select, from_=lhs(label), to=rhs(label))
        for label in labels
    ]


def lhs(label):
    return TablePos('lhs', label)


def rhs(label):
    return TablePos('rhs', label)
