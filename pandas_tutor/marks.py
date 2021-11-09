'''
creates mark specs
'''
import typing as t

import pandas as pd  # type: ignore

from . import util

from .parse_nodes import (Axis, ChainStep, PassThroughCall, RenameCall,
                          SortValuesCall, SubsComparison, SubsEval, SubsSlice,
                          Subscript, SubscriptEl)

from .diagram import Highlight, Mark, Outline, Selection, TablePos
from .run import EvalResult


# yes, step comes from after.step, but we pull it out here to help with
# the type checker
def make_marks(step: ChainStep, before: EvalResult,
               after: EvalResult) -> t.List[Mark]:
    if isinstance(step, SortValuesCall):
        return mark_for_sort_values(step, before, after)
    if isinstance(step, RenameCall):
        return no_marks(step, before, after)
    if isinstance(step, PassThroughCall):
        return no_marks(step, before, after)
    if isinstance(step, Subscript):
        return mark_for_subscript(step, before, after)
    else:
        return no_marks(step, before, after)


# df.sort_values('Name')
def mark_for_sort_values(step: SortValuesCall, before: EvalResult,
                         after: EvalResult) -> t.List[Mark]:
    df = before.df
    args = after.args

    sort_by = args.get('labels', [])
    if isinstance(sort_by, str):
        sort_by = [sort_by]

    sorted_vals = df.index if step.axis == 'index' else df.columns

    highlights = make_highlights(sort_by, selection(step.axis, other=True))
    outlines = make_outlines(sorted_vals, selection(step.axis))
    return [*highlights, *outlines]


def make_highlights(labels: t.Iterable, select: Selection):
    return [
        Highlight(label=label, select=select, anchor='lhs') for label in labels
    ]


def make_outlines(labels: t.Iterable, select: Selection):
    '''
    used as a shorthand when index values don't change, which is most of the
    time
    '''
    return [
        Outline(select=select,
                from_=TablePos('lhs', label),
                to=TablePos('rhs', label)) for label in labels
    ]


# handles:
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
def mark_for_subscript(step: Subscript, before: EvalResult,
                       after: EvalResult) -> t.List[Mark]:
    if step.slicer == 'loc':
        mark_fn = mark_for_loc
    elif step.slicer == 'iloc':
        mark_fn = mark_for_iloc

    # slicer is None, so we need to figure out what kind of slice it is
    elif isinstance(step.slice1, SubsSlice):
        mark_fn = mark_for_iloc
    elif (isinstance(step.slice1, SubsComparison)
          or isinstance(step.slice1, SubsEval)):
        mark_fn = mark_for_loc
    else:
        raise ValueError('weird subscript: {step}')
    return mark_fn(step.slice1, step.slice2, before, after)


def mark_for_iloc(row_slice: t.Optional[SubscriptEl],
                  col_slice: t.Optional[SubscriptEl], before: EvalResult,
                  after: EvalResult) -> t.List[Mark]:
    row_marks = []
    col_marks = []

    if row_slice is None:
        pass
    elif isinstance(row_slice, SubsSlice):
        row_marks = diff_rows(before.df, after.df)
    elif isinstance(row_slice, SubsComparison):
        # TODO: handle comparisons
        row_marks = diff_rows(before.df, after.df)
    elif isinstance(row_slice, SubsEval):
        row_marks = diff_rows(before.df, after.df)
    else:
        raise ValueError(f'weird slice: {row_slice}')

    if col_slice is None:
        pass
    elif isinstance(col_slice, SubsSlice):
        col_marks = diff_cols(before.df, after.df)
    elif isinstance(col_slice, SubsComparison):
        # TODO: should we handle this? pretty uncommon...
        col_marks = diff_cols(before.df, after.df)
    elif isinstance(col_slice, SubsEval):
        col_marks = diff_cols(before.df, after.df)
    else:
        raise ValueError(f'weird slice: {col_slice}')

    return [*col_marks, *row_marks]


def mark_for_loc(row_slice: t.Optional[SubscriptEl],
                 col_slice: t.Optional[SubscriptEl], before: EvalResult,
                 after: EvalResult) -> t.List[Mark]:
    row_marks = []
    col_marks = []

    if row_slice is None:
        pass
    elif isinstance(row_slice, SubsSlice):
        row_marks = diff_rows(before.df, after.df)
    elif isinstance(row_slice, SubsComparison):
        # TODO: handle comparisons
        row_marks = diff_rows(before.df, after.df)
    elif isinstance(row_slice, SubsEval):
        row_marks = diff_rows(before.df, after.df)
    else:
        raise ValueError(f'weird slice: {row_slice}')

    if col_slice is None:
        pass
    elif isinstance(col_slice, SubsSlice):
        col_marks = diff_cols(before.df, after.df)
    elif isinstance(col_slice, SubsComparison):
        # TODO: should we handle this? pretty uncommon...
        col_marks = diff_cols(before.df, after.df)
    elif isinstance(col_slice, SubsEval):
        col_marks = diff_cols(before.df, after.df)
    else:
        raise ValueError(f'weird slice: {col_slice}')

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


def diff_rows(df1, df2):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    '''
    row_matches = util.matching_rows(df1, df2)
    return (make_outlines(row_matches, 'row')  #
            if util.has_diff(df1, row_matches) else [])


def diff_cols(df1, df2):
    '''
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching col
    '''
    col_matches = util.matching_cols(df1, df2)
    return (make_outlines(col_matches, 'column')  #
            if util.has_diff(df1, col_matches) else [])


def no_marks(step: ChainStep, before: EvalResult,
             after: EvalResult) -> t.List[Mark]:
    print(f'Unknown mark for {step.type_}')
    return []


def selection(axis: Axis, other=False) -> Selection:
    if other:
        return 'column' if axis == 'index' else 'row'
    return 'row' if axis == 'index' else 'column'
