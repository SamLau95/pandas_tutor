'''
utilities
'''

import enum
import pdb
import re
import typing as t

import numpy as np
import pandas as pd  # type: ignore

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


def diff_rows(df1: pd.DataFrame,
              df2: pd.DataFrame) -> t.List[t.Tuple[int, int]]:
    '''for each row in df1, returns (row_index, df2_row_index | "NA")'''
    return left_match(df1.index, df2.index)
