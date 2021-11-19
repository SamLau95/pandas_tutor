'''
utilities
'''
from __future__ import annotations
import dataclasses
import io
import base64
import gzip
import typing as t

import matplotlib.pyplot as plt
import matplotlib.figure as figure
import seaborn as sns
import pandas as pd
from pandas.core.groupby.generic import (DataFrameGroupBy, SeriesGroupBy)
from pandas.core.groupby.groupby import GroupBy

# technically dataframe labels can be all sorts of things...
# TODO: handle other index dtypes
Label = t.Union[int, str]
Labels = t.Union[t.List[int], t.List[str]]

HasIndex = t.Union[pd.DataFrame, pd.Series]

Groups = t.Dict[t.Union[str, tuple], pd.Index]


@dataclasses.dataclass
class CodePosition:
    '''
    points to a location within the original code string. both lines and
    columns are 0-indexed
    '''
    line: int
    ch: int

    def __mod__(self, other: CodePosition):
        '''self % other is the position relative to other.line'''
        return CodePosition(self.line - other.line, self.ch)

    def __lt__(self, other: CodePosition):
        return self.line < other.line or self.ch < other.ch

    def __gt__(self, other: CodePosition):
        return self.line > other.line or self.ch > other.ch


@dataclasses.dataclass
class CodeRange:
    '''
    points to a code range within the original code string. both lines and
    columns are 0-indexed.

    these are used to highlight code fragments in the frontend
    '''
    start: CodePosition
    end: CodePosition

    def __sub__(self, other: CodeRange):
        '''
        a range within this CodeRange that doesn't overlap with other. similar
        to set difference. assumes other isn't entirely contained within self,
        and vice versa
        '''
        # non-overlapping
        if self.end < other.start or other.end < self.start:
            return self

        # cut off left tail, common case
        if self.end > other.end:
            return CodeRange(other.end, self.end)

        # cut off right tail
        if self.start < other.start:
            return CodeRange(self.start, other.start)

        return self

    def __mod__(self, pos: CodePosition):
        '''self % pos is the range relative to the starting line of pos'''
        return CodeRange(self.start % pos, self.end % pos)


NULL_LOC = CodeRange(CodePosition(-999, -999), CodePosition(-999, -999))

IndexPair = t.Tuple[Label, Label]


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


def grouping_labels(groupby: GroupBy) -> Labels:
    '''gets ['hello', 'world'] from df.groupby(['hello', 'world'])'''
    # NOTE: when grouping by unnamed sequences, names will contain None
    # >>> full.groupby([test, test2]).grouper.names
    # [None, None]
    return groupby.grouper.names


def is_plottable(obj: t.Any) -> bool:
    return isinstance(obj, (plt.Axes, figure.Figure, sns.FacetGrid))


def base64_encode_plot(fig_or_axes: t.Any) -> str:
    '''
    saves plot as a gzipped, base64 encoded png
    '''
    if not is_plottable(fig_or_axes):
        return ''

    fig = (fig_or_axes.figure
           if hasattr(fig_or_axes, 'figure') else fig_or_axes)

    # saves figure as base64 encoded string
    with io.BytesIO() as buf:
        fig.savefig(buf, format='png')
        buf.seek(0)
        # set mtime=0 to get deterministic gzips for testing
        zipped = gzip.compress(buf.read(), mtime=0)
        return base64.b64encode(zipped).decode()
