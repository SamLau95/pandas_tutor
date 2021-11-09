'''
utilities
'''
import base64
import gzip
import typing as t

import pandas as pd  # type: ignore

from .diagram import Label

IndexPair = t.Tuple[Label, Label]


def gzip_str(s):
    f = gzip.compress(s.encode())
    return base64.b64encode(f).decode()


def mapt(fn, *args):
    "map(fn, *args) and return the result as a tuple."
    return tuple(map(fn, *args))


def matching_rows(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.Index:
    '''find all matching row labels between df1 and df2'''
    return df1.index.intersection(df2.index)


def matching_cols(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.Index:
    '''find all matching col labels between df1 and df2'''
    return df1.columns.intersection(df2.columns)


def has_diff(df1: pd.DataFrame, matches: pd.Index):
    return (len(df1) != len(matches)) or (df1.index != matches).any()
