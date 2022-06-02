"""
has dataclass definitions for final JSON output.
"""

from __future__ import annotations

import dataclasses
from dataclasses import field
from traceback import TracebackException
from typing import Any, List, Tuple, Union

import pandas as pd
import simplejson as json
from typing_extensions import Literal

from .parse_nodes import ParseSyntaxError
from .run import RuntimeErrorResult
from .util import (
    SERIES,
    CodePosition,
    CodeRange,
    JSONScalar,
    Label,
    df_data,
    index_data,
    json_scalar,
    series_data,
    unwrap,
)


@dataclasses.dataclass
class OutputSpec:
    """the final object we'll make into JSON"""

    code: str
    explanation: Explanation

    def to_json(self):
        return json.dumps(
            self, indent=2, default=encode_dataclasses, ignore_nan=True
        )


def _diagram_as_dict(dclass):
    """pass into dataclasses.asdict to rename from_ to from"""
    res = dict(dclass)
    # we want to preserve the original dict order, so we rebuild the dict if we
    # see from_
    if "from_" in res:
        return {"from" if k == "from_" else k: v for k, v in res.items()}
    return res


def encode_dataclasses(obj: Any):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj, dict_factory=_diagram_as_dict)
    return json_scalar(obj)


##############################################################################
# Explanation
##############################################################################


@dataclasses.dataclass
class Diagram:
    type: str
    code_step: str
    fragment: CodeRange
    marks: List[Mark]
    data: Union[DataPair, DataTwoLHS]


@dataclasses.dataclass
class ErrorOutput:
    type: str = field(default="ErrorOutput", init=False, repr=False)
    code_step: str
    message: str


@dataclasses.dataclass
class SyntaxErrorOutput(ErrorOutput):
    type: str = field(default="SyntaxErrorOutput", init=False, repr=False)
    location: CodePosition

    @classmethod
    def from_parse_syntax_error(cls, err: ParseSyntaxError):
        return cls(
            code_step=err.code,
            message=err.error_msg,
            location=err.location.start,
        )


@dataclasses.dataclass
class RuntimeErrorOutput(ErrorOutput):
    type: str = field(default="RuntimeErrorOutput", init=False, repr=False)
    fragment: CodeRange

    @classmethod
    def from_runtime_error_result(cls, result: RuntimeErrorResult):
        tb = TracebackException.from_exception(result.val)
        # get error message from last stack frame
        message = list(tb.format_exception_only())[-1]
        return cls(
            code_step=result.step.code,
            message=message,
            fragment=result.fragment,
        )


@dataclasses.dataclass
class RuntimeErrorInSetup(RuntimeErrorOutput):
    type: str = field(default="RuntimeErrorInSetup", init=False, repr=False)


@dataclasses.dataclass
class RuntimeErrorInChain(RuntimeErrorOutput):
    type: str = field(default="RuntimeErrorInChain", init=False, repr=False)


Explanation = List[Union[Diagram, ErrorOutput]]

##############################################################################
# TablePos
##############################################################################

# the table we're pointing to
Anchor = Literal["lhs", "rhs", "lhs2"]

# the axis we're pointing to
Selection = Literal["column", "row"]

# the index level we're pointing to. None if index is not multi-level
IndexLevel = Union[None, int]

# each TablePos object is serialized as one of these
TablePosType = Literal["axis", "series", "index_level", "cell"]


@dataclasses.dataclass
class TablePos:
    """
    base class that represents a position in a table or series.
    we use this to point to:

    - an single column or row
    - a entire series
    - a single label in the row or column index
    - an entire level in the column or row index
    - the name for an index level
    - a single datum
    """

    # needs to be initialized by subclass
    type: TablePosType = field(init=False)

    def __post_init__(self):
        raise NotImplementedError("subclasses need to initialize self.type")


PosPair = Tuple[TablePos, TablePos]


@dataclasses.dataclass
class AxisPos(TablePos):
    """points to a single column or row for a table"""

    anchor: Anchor
    select: Selection
    label: Label

    def __post_init__(self):
        self.type = "axis"


@dataclasses.dataclass
class SeriesPos(TablePos):
    """points to an entire series"""

    anchor: Anchor
    label: Label = field(default=SERIES, init=False)

    def __post_init__(self):
        self.type = "series"


@dataclasses.dataclass
class IndexLevelPos(TablePos):
    """points to a single level for the index of the column or row labels"""

    anchor: Anchor
    select: Selection
    level: IndexLevel = None

    def __post_init__(self):
        self.type = "index_level"


@dataclasses.dataclass
class CellPos(TablePos):
    """
    points to a single cell in the table, which is uniquely identified by
    the combination of column and row label.
    """

    anchor: Anchor
    row: Label
    # for Series, column is util.SERIES
    column: Label

    def __post_init__(self):
        self.type = "cell"
        self.row = unwrap(self.row)
        self.column = unwrap(self.column)


##############################################################################
# Mark
##############################################################################

# each Mark object is serialized as one of these
MarkType = Literal["using", "map", "map_set", "drop"]


@dataclasses.dataclass
class Mark:
    """base class, don't use directly"""

    type: MarkType = field(init=False)

    def __post_init__(self):
        raise NotImplementedError(
            "subclasses need to initialize self.illustrate"
        )


@dataclasses.dataclass
class Using(Mark):
    """represents the data we used to perform an operation"""

    pos: TablePos

    def __post_init__(self):
        self.type = "using"


@dataclasses.dataclass
class Map(Mark):
    """represents data copied or mapped from lhs to rhs"""

    # from is a Python keyword!
    from_: TablePos
    to: TablePos

    def __post_init__(self):
        self.type = "map"


@dataclasses.dataclass
class MapSet(Mark):
    """
    represents a set of Map objects. the frontend uses this to simplify the
    visualization when there are many small marks to visualize (e.g. many
    cell-to-cell mappings).
    """

    maps: List[Map]

    def __post_init__(self):
        self.type = "map_set"


@dataclasses.dataclass
class Drop(Mark):
    """represents data explicitly removed from the table"""

    pos: TablePos

    def __post_init__(self):
        self.type = "drop"


##############################################################################
# DataPair and DataFrames
##############################################################################

PrevRHS = Literal["prev_rhs"]
NoRHS = Literal["no_rhs"]


@dataclasses.dataclass
class DataPair:
    lhs: Union[DataSpec, PrevRHS]
    rhs: Union[DataSpec, NoRHS]


@dataclasses.dataclass
class DataTwoLHS:
    """two lhs tables, used for joins"""

    lhs: Union[DataSpec, PrevRHS]
    lhs2: DataSpec
    rhs: DataSpec


@dataclasses.dataclass
class DataSpec:
    """base class for a python val we're going to serialize"""

    type: str


@dataclasses.dataclass
class DFSpec(DataSpec):
    type: str = field(default="DataFrame", init=False, repr=False)
    columns: Index
    index: Index
    data: List[List[JSONScalar]]

    @classmethod
    def from_pd(cls, df: pd.DataFrame) -> DFSpec:
        return cls(
            columns=Index.from_pd(df.columns),
            index=Index.from_pd(df.index),
            data=df_data(df),
        )


@dataclasses.dataclass
class SeriesSpec(DataSpec):
    type: str = field(default="Series", init=False, repr=False)
    index: Index
    data: List[JSONScalar]

    @classmethod
    def from_pd(cls, series: pd.Series) -> SeriesSpec:
        return cls(
            index=Index.from_pd(series.index),
            data=series_data(series),
        )


@dataclasses.dataclass
class Index:
    """represents a pandas index in the serialized data"""

    # names of each index level. unnamed levels are None
    names: Tuple

    # for a multi-index, the labels are a list of tuples. this matches the
    # behavior of pd.Index.tolist()
    labels: List[JSONScalar]

    @classmethod
    def from_pd(cls, index: pd.Index) -> Index:
        return cls(names=tuple(index.names), labels=index_data(index))


@dataclasses.dataclass
class GroupBySpec(DFSpec):
    type: str = field(default="DataFrameGroupBy", init=False, repr=False)
    group_data: GroupData


@dataclasses.dataclass
class SeriesGroupBySpec(SeriesSpec):
    type: str = field(default="SeriesGroupBy", init=False, repr=False)
    group_data: GroupData


@dataclasses.dataclass
class GroupData:
    # grouping cols, if we can pull them out
    columns: List[Label]
    groups: List[Group]


@dataclasses.dataclass
class Group:
    """a group maps between dataframe values -> labels that match"""

    # the group name is the unique combo of grouping vals, so if we do:
    # >>> dogs.groupby(['size', 'kids'])
    # then the group names will be: ['small', 'low'], ['small', 'high'], ...
    #
    # the labels appear in the same order as GroupData.col_names
    name: list

    # labels for all rows the group contains
    labels: List[Label]


@dataclasses.dataclass
class ImageSpec(DataSpec):
    """encodes an image as a base64 png"""

    type: str = field(default="Image", init=False, repr=False)
    data: str


@dataclasses.dataclass
class UnhandledData(DataSpec):
    """catch-all for data that we don't know how to handle, like scalars"""

    type: str = field(default="Unhandled", init=False, repr=False)
    data: JSONScalar
