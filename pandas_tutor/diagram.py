'''
has dataclass definitions for final JSON output. keep in sync with sean's
outputs
'''

from __future__ import annotations
import dataclasses
import typing as t


@dataclasses.dataclass
class Diagram:
    type: str
    code_step: str
    mapping: t.List[Mark]
    data_frame: DFPair


Selection = t.Union[t.Literal['column'], t.Literal['row']]
Anchor = t.Union[t.Literal['lhs'], t.Literal['rhs']]


@dataclasses.dataclass
class Highlight:
    illustrate: t.Literal['highlight']
    select: Selection
    anchor: Anchor
    index: int


@dataclasses.dataclass
class Outline:
    illustrate: t.Literal['outline']
    select: Selection
    # from is a Python keyword!
    from_: TablePos
    to: TablePos


Mark = t.Union[Highlight, Outline]


@dataclasses.dataclass
class TablePos:
    anchor: Anchor
    index: int


@dataclasses.dataclass
class DFPair:
    lhs: DF
    rhs: DF


@dataclasses.dataclass
class DF:
    col_names: t.List[str]
    data: t.List[t.Dict]
