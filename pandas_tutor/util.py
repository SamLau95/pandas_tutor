'''
utilities
'''

import re
import typing as t

import pandas as pd  # type: ignore

from .diagram import Null

IndexPair = t.Tuple[int, t.Union[int, Null]]

# https://gist.github.com/bpeterso2000/11277541
QUOTED_STRING_RE = re.compile(
    r"(?P<quote>['\"])(?P<string>.*?)(?<!\\)(?P=quote)")


def literal_strings(arg_as_str: str):
    '''gets ["name", "count"] from the string "df[['name', 'count']]" '''
    return [
        match.group('string')
        for match in QUOTED_STRING_RE.finditer(arg_as_str)
    ]


def item_indexes(seq: t.Sequence):
    '''maps between item and its index'''
    return {item: index for index, item in enumerate(seq)}


def left_match(left: t.Sequence, right: t.Sequence, default='NA'):
    '''(left_index, right_index | default) for each item in left'''
    indexes = item_indexes(right)
    return [(i, indexes.get(item, default)) for i, item in enumerate(left)]


def search(left: t.Sequence, search: t.Sequence):
    '''left's index for each item in search'''
    indexes = item_indexes(left)
    return [indexes[item] for item in search]


def mapt(fn, *args):
    "map(fn, *args) and return the result as a tuple."
    return tuple(map(fn, *args))


def diff_rows(df1: pd.DataFrame, df2: pd.DataFrame) -> t.List[IndexPair]:
    '''for each row in df1, returns (row_index, df2_row_index | "NA")'''
    return left_match(df1.index, df2.index)


def diff_cols(df1: pd.DataFrame, df2: pd.DataFrame) -> t.List[IndexPair]:
    '''for each col in df1, returns (col_index, df2_col_index | "NA")'''
    return left_match(df1.columns, df2.columns)


def has_diff(matches: t.List[IndexPair]):
    return any(left != right for left, right in matches)
