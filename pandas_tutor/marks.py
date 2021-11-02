'''
creates mark specs
'''
import typing as t
import re

from . import util
from .diagram import Highlight, Mark, Outline, TablePos
from .run import EvalResult

# https://gist.github.com/bpeterso2000/11277541
QUOTED_STRING_RE = re.compile(
    r"(?P<quote>['\"])(?P<string>.*?)(?<!\\)(?P=quote)")

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

    # HACK: just checks for strings in the first arg
    sort_cols = [
        match.group('string') for match in QUOTED_STRING_RE.finditer(args[0])
    ]

    highlights = [
        Highlight(index=index, select='column', anchor='lhs')
        for index in util.indexes(df.columns, sort_cols)
    ]

    outlines = [
        Outline(select='row',
                from_=TablePos('lhs', before_index),
                to=TablePos('rhs', after_index))
        for before_index, after_index in util.matching_df_rows(before.df, df)
    ]

    return [*highlights, *outlines]


def no_marks(*args):
    return []
