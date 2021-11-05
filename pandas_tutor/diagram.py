'''
has dataclass definitions for final JSON output.
'''

from __future__ import annotations

import dataclasses
import json
import typing as t

import numpy as np

Null = t.Literal['NA']


def _diagram_as_dict(dclass):
    '''pass into dataclasses.asdict to rename from_ to from'''
    res = dict(dclass)
    # we want to preserve the original dict order, so we rebuild the dict if we
    # see from_
    if 'from_' in res:
        return {'from' if k == 'from_' else k: v for k, v in res.items()}
    return res


class _DiagramEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj, dict_factory=_diagram_as_dict)
        # extras for np objects
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


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
        return json.dumps(items, indent=2, cls=_DiagramEncoder)


Selection = t.Union[t.Literal['column'], t.Literal['row']]
Anchor = t.Union[t.Literal['lhs'], t.Literal['rhs']]


@dataclasses.dataclass
class Highlight:
    select: Selection
    anchor: Anchor
    index: int
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
    index: t.Union[int, Null]


@dataclasses.dataclass
class DFPair:
    lhs: DFSpec
    rhs: DFSpec


@dataclasses.dataclass
class DFSpec:
    col_names: t.List[str]
    row_labels: t.List[str]
    data: t.List[t.List]
