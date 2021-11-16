'''
utilities
'''
import base64
import gzip
import typing as t

import pandas as pd  # type: ignore
from pandas.core.groupby.generic import (  # type: ignore
    DataFrameGroupBy, SeriesGroupBy)

from .diagram import Label

HasIndex = t.Union[pd.DataFrame, pd.Series]

Groups = t.Dict[t.Union[str, tuple], pd.Index]

IndexPair = t.Tuple[Label, Label]


def gzip_str(s):
    f = gzip.compress(s.encode())
    return base64.b64encode(f).decode()


def mapt(fn, *args):
    "map(fn, *args) and return the result as a tuple."
    return tuple(map(fn, *args))


def match_rows(df1: HasIndex, df2: HasIndex, only_if_diff=False) -> pd.Index:
    '''
    find all matching row labels between df1 and df2. if only_if_diff=False
    (default), then return empty list when df1 has exact same rows as df2.
    '''
    # TODO: doesn't handle duplicate values in an index properly, since:
    # >>> a = pd.Index([2, 2])
    # >>> a.intersection(a)
    # Index([2])
    matches = df1.index.intersection(df2.index)
    return (pd.Index([])
            if len(matches) == len(df1.index) or only_if_diff else matches)


def match_cols(df1: pd.DataFrame,
               df2: pd.DataFrame,
               only_if_diff=False) -> pd.Index:
    '''
    find all matching col labels between df1 and df2. if only_if_diff=False
    (default), then return empty list when df1 has exact same cols as df2.
    '''
    matches = df1.columns.intersection(df2.columns)
    return (pd.Index([])
            if len(matches) == len(df1.columns) or only_if_diff else matches)


@t.overload
def ungroup(groupby: SeriesGroupBy) -> pd.Series:
    ...


@t.overload
def ungroup(  # type: ignore # noqa: F811
        groupby: DataFrameGroupBy) -> pd.DataFrame:
    ...


def ungroup(groupby):  # noqa: F811
    '''undos a groupby back into original val'''
    # uses a private attribute...hopefully won't break later :)
    return groupby._selected_obj

    # slower fallback
    # return groupby.transform(lambda x: x)
