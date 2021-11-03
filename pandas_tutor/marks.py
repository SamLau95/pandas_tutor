'''
creates mark specs
'''
import typing as t

from . import util
from .diagram import Highlight, Mark, Outline, TablePos
from .run import EvalResult

MarkMaker = t.Callable[[EvalResult, EvalResult], t.List[Mark]]


def make_marks(type: str, before: EvalResult,
               after: EvalResult) -> t.List[Mark]:
    fn_name = f'mark_for_{type}'
    mark_fn = t.cast(MarkMaker, globals().get(fn_name, no_marks))
    return mark_fn(before, after)


# df.sort_values('Name')
def mark_for_sort_values(before: EvalResult, after: EvalResult):
    df = after.df
    args = t.cast(t.List[str], after.node.children)

    sort_cols = util.literal_strings(args[0])

    cols = [
        Highlight(index=index, select='column', anchor='lhs')
        for index in util.search(df.columns, sort_cols)
    ]

    rows = [
        Outline(select='row',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in util.diff_rows(before.df, df)
    ]

    return [*cols, *rows]


# handles:
# df.loc[1:5, ['Name', 'Count']]
# df.iloc[2:5, 1:4]
# df[df['Count'] > 10000]
def mark_for_slice(before: EvalResult, after: EvalResult):
    # HACK: special case: when there's a boolean op in the slice, use
    # sort_values logic. but this won't handle cases like: df[df['booleans']]
    args = t.cast(t.List[str], after.node.children)
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


def no_marks(before: EvalResult, after: EvalResult):
    print(f'Unknown mark for {after.node}')
    return []
