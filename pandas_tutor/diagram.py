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
    index: int


@dataclasses.dataclass
class DFPair:
    lhs: DFSpec
    rhs: DFSpec


@dataclasses.dataclass
class DFSpec:
    col_names: t.List[str]
    data: t.List[t.Dict]
