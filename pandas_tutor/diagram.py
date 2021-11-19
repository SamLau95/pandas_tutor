'''
has dataclass definitions for final JSON output.
'''

from __future__ import annotations

import dataclasses
from dataclasses import field
import simplejson as json
import typing as t

import numpy as np
import pandas as pd

# technically dataframe labels can be all sorts of things...
# TODO: handle other index dtypes
Label = t.Union[int, str]
Labels = t.Union[t.List[int], t.List[str]]


def _diagram_as_dict(dclass):
    '''pass into dataclasses.asdict to rename from_ to from'''
    res = dict(dclass)
    # we want to preserve the original dict order, so we rebuild the dict if we
    # see from_
    if 'from_' in res:
        return {'from' if k == 'from_' else k: v for k, v in res.items()}
    return res


def encode_pd_objs(obj: t.Any):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj, dict_factory=_diagram_as_dict)

    # extras for np and pandas objects

    # note that this doesn't catch np.nan! python's json module natively
    # encodes np.nan to NaN for whatever reason, which is why need to use
    # simplejson for json encoding
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


@dataclasses.dataclass
class Diagram:
    type: str
    code_step: str
    mapping: t.List[Mark]

    # although we call this data_frame, technically it can hold any type of
    # data, like series or groupbys
    data_frame: DataPair

    def to_dict(self):
        return dataclasses.asdict(self, dict_factory=_diagram_as_dict)

    # a bit clunky since we'll also use this for ErrorOutput, but :shrug:
    @classmethod
    def to_json(cls, items: t.Any):
        return json.dumps(items,
                          indent=2,
                          default=encode_pd_objs,
                          ignore_nan=True)


@dataclasses.dataclass
class ErrorOutput:
    type: str = field(default='ErrorOutput', init=False, repr=False)
    code_step: str
    message: str

    def to_dict(self):
        return dataclasses.asdict(self, dict_factory=_diagram_as_dict)


Explanation = t.List[t.Union[Diagram, ErrorOutput]]

Selection = t.Literal['column', 'row']
Anchor = t.Literal['lhs', 'rhs']


@dataclasses.dataclass
class Highlight:
    select: Selection
    anchor: Anchor
    label: Label
    illustrate: t.Literal['highlight'] = 'highlight'


@dataclasses.dataclass
class Outline:
    select: Selection
    # from is a Python keyword!
    from_: TablePos
    to: TablePos
    illustrate: t.Literal['outline'] = 'outline'


Mark = t.Union[Highlight, Outline]


@dataclasses.dataclass
class TablePos:
    anchor: Anchor
    label: Label


@dataclasses.dataclass
class DataPair:
    lhs: DataSpec
    rhs: DataSpec


@dataclasses.dataclass
class DFSpec:
    type: str = field(default='DataFrame', init=False, repr=False)
    col_names: Labels
    row_labels: Labels
    data: t.List[t.List]


@dataclasses.dataclass
class SeriesSpec:
    type: str = field(default='Series', init=False, repr=False)
    row_labels: Labels
    data: t.List


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
    col_names: Labels
    groups: t.List[Group]


@dataclasses.dataclass
class Group:
    '''a group maps between dataframe values -> labels that match'''
    # the group name is the unique combo of grouping vals, so if we do:
    # >>> dogs.groupby(['size', 'kids'])
    # then the group names will be: ('small', 'low'), ('small', 'high'), ...
    #
    # the labels appear in the same order as GroupData.col_names
    name: list

    # labels for all rows the group contains
    labels: Labels


@dataclasses.dataclass
class ImageSpec:
    '''encodes an image as a gzipped base64 png'''
    type: str = field(default='Image', init=False, repr=False)
    data: str


@dataclasses.dataclass
class UnhandledData:
    '''catch-all for data that we don't know how to handle, like scalars'''
    type: str = field(default='Unhandled', init=False, repr=False)
    data: t.Any


DataSpec = t.Union[UnhandledData, DFSpec, SeriesSpec, GroupBySpec,
                   SeriesGroupBySpec, ImageSpec, ]
