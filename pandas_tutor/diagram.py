"""
has dataclass definitions for final JSON output.
"""

from __future__ import annotations

import dataclasses
from traceback import TracebackException
import typing as t
from dataclasses import field
import pandas as pd

import simplejson as json

from .parse_nodes import ParseSyntaxError
from .run import RuntimeErrorResult
from .util import CodePosition, CodeRange, JSONScalar, Label


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


def encode_dataclasses(obj: t.Any):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj, dict_factory=_diagram_as_dict)
    return obj


##############################################################################
# Explanation
##############################################################################


@dataclasses.dataclass
class Diagram:
    type: str
    code_step: str
    fragment: CodeRange
    marks: t.List[Mark]
    data: DataPair


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


Explanation = t.List[t.Union[Diagram, ErrorOutput]]

##############################################################################
# TablePos
##############################################################################

# the table we're pointing to
Anchor = t.Literal["lhs", "rhs"]

# the axis we're pointing to
Selection = t.Literal["column", "row"]

# the index level we're pointing to. None if index is not multi-level
IndexLevel = t.Union[None, int]

# each TablePos object is serialized as one of these
TablePosType = t.Literal[
    "axis", "series", "label", "index_level", "index_name", "datum"
]


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
    label: Label = field(default="pandas.Series", init=False)

    def __post_init__(self):
        self.type = "series"


@dataclasses.dataclass
class LabelPos(TablePos):
    """
    points to a single label for a column or row. used for functions like
    rename()
    """

    anchor: Anchor
    select: Selection
    label: Label
    level: IndexLevel = None

    def __post_init__(self):
        self.type = "label"


@dataclasses.dataclass
class IndexLevelPos(TablePos):
    """points to a single level for the index of the column or row labels"""

    anchor: Anchor
    select: Selection
    level: IndexLevel = None

    def __post_init__(self):
        self.type = "index_level"


@dataclasses.dataclass
class IndexNamePos(TablePos):
    """
    points to the name for a level of the index of the column or row labels.
    used for functions like rename_axis() which renames index levels
    """

    anchor: Anchor
    select: Selection
    level: IndexLevel = None

    def __post_init__(self):
        self.type = "index_name"


@dataclasses.dataclass
class DatumPos(TablePos):
    """points to a single datum in the table"""

    anchor: Anchor
    column: Label
    row: Label

    def __post_init__(self):
        self.type = "datum"


##############################################################################
# Mark
##############################################################################

# each Mark object is serialized as one of these
MarkType = t.Literal["using", "map", "drop"]


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
class Drop(Mark):
    """represents data explicitly removed from the table"""

    pos: TablePos

    def __post_init__(self):
        self.type = "drop"


##############################################################################
# DataPair and DataFrames
##############################################################################

PrevRHS = t.Literal["prev_rhs"]
NoRHS = t.Literal["no_rhs"]


@dataclasses.dataclass
class DataPair:
    lhs: t.Union[DataSpec, PrevRHS]
    rhs: t.Union[DataSpec, NoRHS]


@dataclasses.dataclass
class DataSpec:
    """base class for a python val we're going to serialize"""

    type: str


@dataclasses.dataclass
class Index:
    """represents a pandas index in the serialized data"""

    # names of each index level. unnamed levels are None
    names: t.Tuple

    # for a multi-index, the labels are a list of tuples. this matches the
    # behavior of pd.Index.tolist()
    labels: t.List[Label]

    @classmethod
    def from_pd(cls, index: pd.Index) -> Index:
        return cls(names=tuple(index.names), labels=index.tolist())


@dataclasses.dataclass
class DFSpec(DataSpec):
    type: str = field(default="DataFrame", init=False, repr=False)
    columns: Index
    index: Index
    data: t.List[t.List[JSONScalar]]


@dataclasses.dataclass
class SeriesSpec(DataSpec):
    type: str = field(default="Series", init=False, repr=False)
    index: Index
    data: t.List[JSONScalar]


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
    columns: t.List[Label]
    groups: t.List[Group]


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
    labels: t.List[Label]


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
