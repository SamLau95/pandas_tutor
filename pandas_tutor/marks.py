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

    highlights = [
        Highlight(index=index, select='column', anchor='lhs')
        for index in util.search(df.columns, sort_cols)
    ]

    outlines = [
        Outline(select='row',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in util.diff_rows(before.df, df)
    ]

    return [*highlights, *outlines]


def mark_for_slice(before: EvalResult, after: EvalResult):
    df = after.df
    outlines = [
        Outline(select='row',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in util.diff_rows(before.df, df)
    ]
    return outlines


def no_marks(before: EvalResult, after: EvalResult):
    print(f'Unknown mark for {after.node}')
    return []
