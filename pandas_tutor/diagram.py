'''
has dataclass definitions for final JSON output.
'''

from __future__ import annotations

import dataclasses
import simplejson as json
import typing as t

import numpy as np
import pandas as pd  # type: ignore

# technically dataframe labels can be all sorts of things...
# TODO: handle other index dtypes
Label = t.Union[int, str]


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
    data_frame: DFPair

    def to_dict(self):
        return dataclasses.asdict(self, dict_factory=_diagram_as_dict)

    @classmethod
    def to_json(cls, items: t.Union[t.List[Diagram], Diagram]):
        return json.dumps(items,
                          indent=2,
                          default=encode_pd_objs,
                          ignore_nan=True)


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
class DFPair:
    lhs: DFSpec
    rhs: DFSpec


@dataclasses.dataclass
class DFSpec:
    col_names: t.List[str]
    row_labels: t.List[str]
    data: t.List[t.List]
