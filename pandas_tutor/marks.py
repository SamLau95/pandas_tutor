'''
creates mark specs
'''
import typing as t
import pandas as pd

from .parse_nodes import (ChainStep, PassThroughCall, RenameCall,
                          SortValuesCall, Subscript)

from . import util
from .diagram import Highlight, Mark, Outline, TablePos
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
        return no_marks(step, before, after)
    else:
        return no_marks(step, before, after)


# df.sort_values('Name')
def mark_for_sort_values(step: SortValuesCall, before: EvalResult,
                         after: EvalResult) -> t.List[Mark]:
    df = before.df
    args = after.args

    used_for_sorting = args.get('labels', [])
    if isinstance(used_for_sorting, str):
        used_for_sorting = [used_for_sorting]

    highlight_axis = 'column' if step.axis == 'index' else 'row'
    outline_axis = 'row' if step.axis == 'index' else 'column'

    what_was_sorted = df.index if step.axis == 'index' else df.columns

    highlights = [
        Highlight(label=label, select=highlight_axis, anchor='lhs')
        for label in used_for_sorting
    ]

    outlines = [
        Outline(select=outline_axis,
                from_=TablePos('lhs', label),
                to=TablePos('rhs', label)) for label in what_was_sorted
    ]

    return [*highlights, *outlines]


# handles:
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
def mark_for_subscript(step: ChainStep, before: EvalResult,
                       after: EvalResult) -> t.List[Mark]:
    # HACK: special case: when there's a boolean op in the slice, use
    # sort_values logic. but this won't handle cases like: df[df['booleans']]
    args = t.cast(t.List[str], after.step.children)
    if any(map(util.has_boolean_op, args)):
        return mark_for_sort_values(before, after)

    df = after.df

    row_diffs = util.diff_rows(before.df, df)
    col_diffs = util.diff_cols(before.df, df)

    # only make marks if there is at least one mismatch
    rows = [
        Outline(select='row',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in row_diffs
    ] if util.has_diff(row_diffs) else []

    cols = [
        Outline(select='column',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in util.diff_cols(before.df, df)
    ] if util.has_diff(col_diffs) else []

    return [*cols, *rows]


def no_marks(step: ChainStep, before: EvalResult,
             after: EvalResult) -> t.List[Mark]:
    print(f'Unknown mark for {step.type_}')
    return []
