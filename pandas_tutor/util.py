"""
utilities
"""
from __future__ import annotations

import base64
import dataclasses
import io
import itertools
import warnings
from collections.abc import Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Hashable,
    List,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)
from warnings import warn

import numpy as np
import pandas as pd
import pandas.core.groupby.base
from pandas.core.groupby.generic import DataFrameGroupBy, SeriesGroupBy
from pandas.core.groupby.groupby import GroupBy
from pandas.core.reshape.merge import _MergeOperation

# Literal only added in Python 3.8
from typing_extensions import Literal, TypeGuard

if TYPE_CHECKING:
    from pandas_tutor.diagram import MapSet  # noqa: F401

# functions that aggregate groups together
pd_agg_funcs: List[str] = pandas.core.groupby.base.reduction_kernels

T = TypeVar("T")

Axis = Literal["index", "columns"]
Slicer = Literal["loc", "iloc", None]

# A Label is a value that came from pandas Index. It's a tuple of values
# if we have a multi-index, or a single value otherwise.
Label = Hashable
LabelPair = Tuple[Label, Label]

HasIndex = Union[pd.DataFrame, pd.Series]

Groups = Dict[Union[str, tuple], pd.Index]

JSONScalar = Union[int, float, str, bool, None]

# placeholder column for pd.Series
SERIES = "pandas.Series"


def first(iterable: Iterable[T]) -> T:
    """the first element of an iterable."""
    return next(iter(iterable))


def second(iterable: Iterable[T]) -> T:
    """the second element of an iterable."""
    it = iter(iterable)
    next(it)
    return next(it)


def mapt(fn, *args):
    "map(fn, *args) and return the result as a tuple."
    return tuple(map(fn, *args))


def flatmap(fn, *args):
    "map(fn, *args) and return the result as a flattened iterable."
    return itertools.chain.from_iterable(map(fn, *args))


def is_list_like(obj: Any) -> bool:
    """
    checks whether obj is a list-like. we need this because we don't usually
    want to do list(string), but we want to convert other types of list-like
    things to lists
    """
    return not isinstance(obj, str) and isinstance(obj, Iterable)


def listify(obj: Any) -> List:
    """if obj is a scalar, returns [obj]"""
    return obj if is_list_like(obj) else [obj]


def tuplify(obj: Any) -> Tuple:
    """if obj is a scalar, returns (obj, )"""
    return obj if is_list_like(obj) else (obj,)


@overload
def unwrap(obj: Tuple[T]) -> Union[Tuple[T], T]:
    ...


@overload
def unwrap(obj: List[T]) -> Union[List[T], T]:
    ...


@overload
def unwrap(obj: Label) -> Label:
    ...


def unwrap(obj):
    """unwrap obj if single element"""
    return obj if not is_list_like(obj) else obj[0] if len(obj) == 1 else obj


def split_by(
    seq: Sequence[T], indexes: Sequence[int]
) -> Tuple[Tuple[T, ...], Tuple[T, ...]]:
    """
    returns two tuples, one with the elements at the given indexes, and one
    with the rest of the elements.
    """
    # can't use sets since we need to preserve order
    not_in = [i for i in range(len(seq)) if i not in indexes]
    return tuple(seq[i] for i in indexes), tuple(seq[i] for i in not_in)


@dataclasses.dataclass
class CodePosition:
    """
    points to a location within the original code string. both lines and
    columns are 0-indexed
    """

    line: int
    ch: int

    def __mod__(self, other: CodePosition):
        """self % other is the position relative to other.line"""
        return CodePosition(self.line - other.line, self.ch)

    def __lt__(self, other: CodePosition):
        return (
            self.line < other.line
            if self.line != other.line
            else self.ch < other.ch
        )

    def __gt__(self, other: CodePosition):
        return (
            self.line > other.line
            if self.line != other.line
            else self.ch > other.ch
        )

    def __str__(self):
        return f"({self.line}:{self.ch})"


@dataclasses.dataclass
class CodeRange:
    """
    points to a code range within the original code string. both lines and
    columns are 0-indexed.

    these are used to highlight code fragments in the frontend
    """

    start: CodePosition
    end: CodePosition

    def __sub__(self, other: CodeRange):
        """
        a range within this CodeRange that doesn't overlap with other. similar
        to set difference. assumes the CodeRanges only partially overlap
        """
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

    def __or__(self, other: CodeRange):
        """
        minimum CodeRange that contains both self and other
        """
        return CodeRange(
            start=self.start if self.start < other.start else other.start,
            end=self.end if self.end > other.end else other.end,
        )

    def __mod__(self, pos: CodePosition):
        """self % pos is the range relative to the starting line of pos"""
        return CodeRange(self.start % pos, self.end % pos)

    def __str__(self):
        return f"{self.start} -> {self.end}"


##############################################################################
# pandas
##############################################################################


@overload
def positions_to_labels(
    positions: Union[int, Label],
    df: HasIndex,
    slicer: Slicer = "iloc",
    axis: Axis = "index",
) -> Label:
    ...


@overload
def positions_to_labels(  # noqa: F811
    positions: list,  # type: ignore
    df: HasIndex,
    slicer: Slicer = "iloc",
    axis: Axis = "index",
) -> List[Label]:
    ...


def positions_to_labels(  # noqa: F811
    positions,
    df,
    slicer: Slicer = "iloc",
    axis: Axis = "index",
):
    """
    convert positional indexes like [2, 3, 0] to labels.
    doesn't do anything if slicer isn't iloc.
    if positions is a single number, also returns a single label.
    """
    if slicer != "iloc":
        return positions
    if axis != "index" and isinstance(df, pd.Series):
        warn("tried to convert column labels for a series")
        return positions

    labels = cast(pd.Index, df.columns if axis == "columns" else df.index)
    return labels[positions]


def match_rows(df1: HasIndex, df2: HasIndex, only_if_diff=True) -> pd.Index:
    """
    find all matching row labels between df1 and df2. if only_if_diff=True
    (default), then return empty index when df1 has same rows as df2.
    """
    # TODO: doesn't handle duplicate values in an index properly, since:
    # >>> a = pd.Index([2, 2])
    # >>> a.intersection(a)
    # Index([2])
    matches = df1.index.intersection(df2.index)  # type: ignore
    return (
        pd.Index([], dtype="int64")
        if (len(matches) == len(df1.index) and only_if_diff)
        else matches
    )


def match_cols(
    df1: pd.DataFrame, df2: pd.DataFrame, only_if_diff=True
) -> pd.Index:
    """
    find all matching col labels between df1 and df2. if only_if_diff=True
    (default), then return empty index when df1 has same cols as df2.
    """
    matches = df1.columns.intersection(df2.columns)
    return (
        pd.Index([], dtype="int64")
        if (len(matches) == len(df1.columns) and only_if_diff)
        else matches
    )


def is_series(obj: Any) -> TypeGuard[pd.Series]:
    return isinstance(obj, pd.Series)


def is_dataframe(obj: Any) -> TypeGuard[pd.DataFrame]:
    return isinstance(obj, pd.DataFrame)


def is_pd(obj: Any) -> TypeGuard[Union[pd.DataFrame, pd.Series]]:
    return is_series(obj) or is_dataframe(obj)


def is_multi(index: pd.Index) -> TypeGuard[pd.MultiIndex]:
    return isinstance(index, pd.MultiIndex)


def level_number(index: pd.Index, level: str | int) -> int:
    "converts a name of a level to the level's integer index if needed"
    return (
        index.names.index(level)
        if isinstance(level, str)
        else level % len(index.names)
    )


def first_iloc(index: pd.Index, label: Label) -> int:
    """
    returns the first position of a label in an index.
    """
    for i, lab in enumerate(index):
        if lab == label:
            return i
    return -1


##############################################################################
# multiindex
##############################################################################

# pair of multi-index labels
_MultiLabelPair = Tuple[Tuple[Label, ...], Tuple[Label, ...]]


def cell_labels(
    index1: Iterable[Label], index2: Iterable[Label]
) -> Tuple[LabelPair]:
    """returns (row, column) labels"""
    return tuple(itertools.product(index1, index2))  # type: ignore


def push_levels(
    from_: Iterable[Label], to: Iterable[Label], levels: List[int]
) -> Iterable[Tuple[LabelPair, LabelPair]]:
    """
    pushes levels from_ -> to. used to map cells during reshaping operations.
    returns original and new label pairs.
    """
    orig = cell_labels(from_, to)

    # if we're pushing into a series, we need to handle the placeholder
    iter_to = to if SERIES not in to else [tuple()]

    # wrap values in tuples to make iteration easier
    wrapped_orig = cast(
        List[_MultiLabelPair],
        list(itertools.product(map(tuplify, from_), map(tuplify, iter_to))),
    )

    new: List[LabelPair] = []
    for left, right in wrapped_orig:
        move, stay = split_by(left, levels)
        new.append(mapt(unwrap, (stay, (*right, *move))))

    return zip(orig, new)


def push_level(from_: Label, to: Label, levels: List[int]) -> LabelPair:
    """pushes levels from_ -> to for one label pair"""
    # if we're pushing into a series, we need to handle the placeholder
    to = to if to != SERIES else tuple()
    left = tuplify(from_)
    right = tuplify(to)
    move, stay = split_by(left, levels)
    return mapt(unwrap, (stay, (*right, *move)))


##############################################################################
# groupby
##############################################################################


@overload
def ungroup(obj: Union[SeriesGroupBy, pd.Series]) -> pd.Series:
    ...


@overload
def ungroup(  # type: ignore # noqa: F811
    obj: Union[DataFrameGroupBy, pd.DataFrame]  # noqa: F811
) -> pd.DataFrame:
    ...


def ungroup(obj):  # noqa: F811
    """
    undos a groupby back into original val. if obj isn't grouped, returns obj
    """
    if isinstance(obj, (SeriesGroupBy, DataFrameGroupBy)):
        # uses a private attribute...hopefully won't break later :)
        return obj._selected_obj
    return obj

    # slower fallback
    # return groupby.transform(lambda x: x)


def grouping_labels(groupby: GroupBy) -> List[Label]:
    """gets ['hello', 'world'] from df.groupby(['hello', 'world'])"""
    # NOTE: when grouping by unnamed sequences, names will contain None
    # >>> full.groupby([test, test2]).grouper.names
    # [None, None]
    return groupby.grouper.names


def get_groups(groupby: Union[SeriesGroupBy, DataFrameGroupBy]) -> Groups:
    """
    gets mapping of group keys -> dataframe labels.
    """
    # when the group keys includes NaN, groupby.groups freaks out, so we use a
    # workaround by getting the group indices first, then recovering the labels
    try:
        return cast(Groups, groupby.groups)
    except ValueError:
        index = ungroup(groupby).index
        groups = {
            key: index[indices] for key, indices in groupby.indices.items()
        }
        return cast(Groups, groups)


##############################################################################
# merge
##############################################################################


def get_join_info(*args, **kwargs) -> Tuple[pd.Index, pd.Index, pd.Index]:
    """
    call using same signature as pd.merge. returns (index of merged df, indexer
    for lhs, indexer for lhs2). uses pandas internals.

    >>> op = _MergeOperation(baby, nyt2,
    ...                      left_on='Name', right_on='nyt_name', how='left')
    >>> join_index, left_indexer, right_indexer = op._get_join_info()
    >>> join_index, left_indexer, right_indexer
    (Int64Index([0, 1, 2, 3, 4], dtype='int64'),
     array([1, 2, 3, 0, 4]),
     array([ 1,  0,  0, -1, -1]))
    """
    op = _MergeOperation(*args, **kwargs)
    return op._get_join_info()  # type: ignore


##############################################################################
# serializing
##############################################################################


def is_plottable(obj: Any) -> bool:
    fig = obj.figure if hasattr(obj, "figure") else obj
    return hasattr(fig, "savefig")


def base64_encode_plot(fig_or_axes: Any) -> str:
    """
    saves plot as a gzipped, base64 encoded png
    """
    if not is_plottable(fig_or_axes):
        return ""

    fig = fig_or_axes.figure if hasattr(fig_or_axes, "figure") else fig_or_axes

    # saves figure as base64 encoded string
    with io.BytesIO() as buf:
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        # set mtime=0 to get deterministic gzips for testing
        # zipped = gzip.compress(buf.read(), mtime=0)
        return base64.b64encode(buf.read()).decode()


def json_scalar(obj: Any) -> JSONScalar:
    """
    transforms special pandas / numpy value to a value that can be
    serialized to json
    """
    if pd.isnull(obj):
        return None
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp) or isinstance(obj, pd.Timedelta):
        return str(obj)

    # groupby().plot() creates a Series with AxesSubplots as data values.
    # weird!
    if obj.__class__.__name__ == "AxesSubplot":
        return str(obj)

    return obj


def index_data(index: pd.Index) -> List[JSONScalar]:
    return [json_scalar(val) for val in index.to_list()]


def series_data(series: pd.Series) -> List[JSONScalar]:
    return [json_scalar(val) for val in series.to_numpy()]


def df_data(df: pd.DataFrame) -> List[List[JSONScalar]]:
    return [[json_scalar(val) for val in row] for row in df.to_numpy()]


##############################################################################
# memory
##############################################################################


def mem_used(obj: Any) -> float:
    if isinstance(obj, pd.DataFrame):
        return obj.memory_usage(deep=True).sum()
    elif isinstance(obj, pd.Series):
        return obj.memory_usage(deep=True)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from pympler.asizeof import asizeof
        return asizeof(obj)


KB = 2**10
MB = 2**20
MEM_LIMIT = 1 * MB


def mem_as_str(mem: float) -> str:
    if mem >= MB:
        # 2 decimal places
        return f"{mem / MB:.2f} MB"
    elif mem >= KB:
        return f"{mem / KB:.2f} KB"
    else:
        return f"{mem} B"


def too_much_mem_msg(mem: float):
    return (
        f"Your total data uses {mem_as_str(mem)} of memory, which exceeds "
        f"the maximum of {mem_as_str(MEM_LIMIT)} that this tool supports."
    )
