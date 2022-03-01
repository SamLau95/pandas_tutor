'''
has dataclass definitions for final JSON output.
'''

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
    '''the final object we'll make into JSON'''
    code: str
    explanation: Explanation

    def to_json(self):
        return json.dumps(self,
                          indent=2,
                          default=encode_dataclasses,
                          ignore_nan=True)


def _diagram_as_dict(dclass):
    '''pass into dataclasses.asdict to rename from_ to from'''
    res = dict(dclass)
    # we want to preserve the original dict order, so we rebuild the dict if we
    # see from_
    if 'from_' in res:
        return {'from' if k == 'from_' else k: v for k, v in res.items()}
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
    mapping: t.List[Mark]

    # although we call this data_frame, technically it can hold any type of
    # data, like series or groupbys
    data_frame: DataPair


@dataclasses.dataclass
class ErrorOutput:
    type: str = field(default='ErrorOutput', init=False, repr=False)
    code_step: str
    message: str


@dataclasses.dataclass
class SyntaxErrorOutput(ErrorOutput):
    type: str = field(default='SyntaxErrorOutput', init=False, repr=False)
    location: CodePosition

    @classmethod
    def from_parse_syntax_error(cls, err: ParseSyntaxError):
        return cls(code_step=err.code,
                   message=err.error_msg,
                   location=err.location.start)


@dataclasses.dataclass
class RuntimeErrorOutput(ErrorOutput):
    type: str = field(default='RuntimeErrorOutput', init=False, repr=False)
    fragment: CodeRange

    @classmethod
    def from_runtime_error_result(cls, result: RuntimeErrorResult):
        tb = TracebackException.from_exception(result.val)
        # get error message from last stack frame
        message = list(tb.format_exception_only())[-1]
        return cls(code_step=result.step.code,
                   message=message,
                   fragment=result.fragment)


@dataclasses.dataclass
class RuntimeErrorInSetup(RuntimeErrorOutput):
    type: str = field(default='RuntimeErrorInSetup', init=False, repr=False)


@dataclasses.dataclass
class RuntimeErrorInChain(RuntimeErrorOutput):
    type: str = field(default='RuntimeErrorInChain', init=False, repr=False)


Explanation = t.List[t.Union[Diagram, ErrorOutput]]

##############################################################################
# Mark
##############################################################################

Selection = t.Literal['column', 'row']
Anchor = t.Literal['lhs', 'rhs']
MarkType = t.Literal['highlight', 'outline', 'crossout']


@dataclasses.dataclass
class Mark:
    illustrate: MarkType = field(init=False)
    select: Selection

    def __post_init__(self):
        raise NotImplementedError(
            'subclasses need to initialize self.illustrate')


@dataclasses.dataclass
class Highlight(Mark):
    anchor: Anchor
    label: Label

    def __post_init__(self):
        self.illustrate = 'highlight'


@dataclasses.dataclass
class Outline(Mark):
    # from is a Python keyword!
    from_: TablePos
    to: TablePos

    def __post_init__(self):
        self.illustrate = 'outline'


@dataclasses.dataclass
class CrossOut(Outline):
    def __post_init__(self):
        self.illustrate = 'crossout'


@dataclasses.dataclass
class TablePos:
    anchor: Anchor
    label: Label


##############################################################################
# DataPair and DataFrames
##############################################################################

PrevRHS = t.Literal['prev_rhs']
NoRHS = t.Literal['no_rhs']


@dataclasses.dataclass
class DataPair:
    lhs: t.Union[DataSpec, PrevRHS]
    rhs: t.Union[DataSpec, NoRHS]


@dataclasses.dataclass
class DataSpec:
    '''base class for a python val we're going to serialize'''
    type: str


@dataclasses.dataclass
class Index:
    '''represents a pandas index in the serialized data'''
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
    type: str = field(default='DataFrame', init=False, repr=False)
    columns: Index
    index: Index
    data: t.List[t.List[JSONScalar]]


@dataclasses.dataclass
class SeriesSpec(DataSpec):
    type: str = field(default='Series', init=False, repr=False)
    index: Index
    data: t.List[JSONScalar]


@dataclasses.dataclass
class GroupBySpec(DFSpec):
    type: str = field(default='DataFrameGroupBy', init=False, repr=False)
    group_data: GroupData


@dataclasses.dataclass
class SeriesGroupBySpec(SeriesSpec):
    type: str = field(default='SeriesGroupBy', init=False, repr=False)
    group_data: GroupData


@dataclasses.dataclass
class GroupData:
    # grouping cols, if we can pull them out
    columns: t.List[Label]
    groups: t.List[Group]


@dataclasses.dataclass
class Group:
    '''a group maps between dataframe values -> labels that match'''
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
    '''encodes an image as a base64 png'''
    type: str = field(default='Image', init=False, repr=False)
    data: str


@dataclasses.dataclass
class UnhandledData(DataSpec):
    '''catch-all for data that we don't know how to handle, like scalars'''
    type: str = field(default='Unhandled', init=False, repr=False)
    data: JSONScalar
