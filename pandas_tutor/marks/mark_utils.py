"""
utils only used for making marks
"""
import itertools
from typing import Callable, Iterable, List, Tuple

import pandas as pd

from .. import util
from ..diagram import (
    Anchor,
    AxisPos,
    CellPos,
    Drop,
    IndexLevel,
    IndexLevelPos,
    Map,
    MapSet,
    Mark,
    PosPair,
    Selection,
    SeriesPos,
    TablePos,
    Using,
)
from ..parse_nodes import Axis
from ..util import Label, LabelPair


def diff_dfs(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights. only outputs when there is at least one mismatching row
    / col
    """
    rows = diff_rows(df1, df2)
    cols = diff_cols(df1, df2)
    return [*cols, *rows]


def diff_rows(df1: util.HasIndex, df2: util.HasIndex, only_if_diff=True):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights.
    """
    row_matches = util.match_rows(df1, df2, only_if_diff)
    return make_maps(row_matches, "row")


def diff_cols(df1: pd.DataFrame, df2: pd.DataFrame, only_if_diff=True):
    """
    when we just want to draw arrows between different rows and cols without
    special highlights.
    """
    col_matches = util.match_cols(df1, df2, only_if_diff)
    return make_maps(col_matches, "column")


def no_marks(*args) -> List[Mark]:
    # print(f'Unknown mark for {step.type_}')
    return []


def selection(axis: Axis, other=False) -> Selection:
    if other:
        return "column" if axis == "index" else "row"
    return "row" if axis == "index" else "column"


def make_usings(
    labels: Iterable, select: Selection, anchor: Anchor = "lhs"
) -> List[Mark]:
    """
    shorthand to make a highlight for each column/row in labels
    """
    return [Using(AxisPos(anchor, select, label)) for label in labels]


def make_maps(labels: Iterable, select: Selection) -> List[Mark]:
    """
    shorthand when index values don't change, which is most of the time
    """
    return [
        Map(from_=lhs(select, label), to=rhs(select, label)) for label in labels
    ]


def make_drops(
    labels: Iterable, select: Selection, anchor: Anchor = "lhs"
) -> List[Mark]:
    """
    shorthand for crossouts
    """
    return [Drop(AxisPos(anchor, select, label)) for label in labels]


def using_and_map(left_pos: TablePos, right_pos: TablePos) -> List[Mark]:
    """Map left to right and Using both"""
    return [Using(left_pos), Using(right_pos), Map(left_pos, right_pos)]


def lhs(select: Selection, label: Label) -> AxisPos:
    """shorthand for a column/row in lhs"""
    return AxisPos("lhs", select, label)


def rhs(select: Selection, label: Label) -> AxisPos:
    """shorthand for a column/row in rhs"""
    return AxisPos("rhs", select, label)


def lhs2(select: Selection, label: Label) -> AxisPos:
    """shorthand for a column/row in lhs2"""
    return AxisPos("lhs2", select, label)


def lhs_index(select: Selection, level: IndexLevel) -> IndexLevelPos:
    """shorthand for an index level in lhs"""
    return IndexLevelPos("lhs", select, level)


def rhs_index(select: Selection, level: IndexLevel) -> IndexLevelPos:
    """shorthand for an index level in rhs"""
    return IndexLevelPos("rhs", select, level)


def lhs2_index(select: Selection, level: IndexLevel) -> IndexLevelPos:
    """shorthand for an index level in lhs2"""
    return IndexLevelPos("lhs2", select, level)


def lhs_series() -> SeriesPos:
    """shorthand for the lhs series"""
    return SeriesPos("lhs")


def rhs_series() -> SeriesPos:
    """shorthand for the rhs series"""
    return SeriesPos("rhs")


def lhs2_series() -> SeriesPos:
    """shorthand for the lhs2 series"""
    return SeriesPos("lhs2")


def by_row(pair: Tuple[CellPos, CellPos]) -> Label:
    """grouper for CellPos pairs. returns the row label of the original cell"""
    cell, _ = pair
    return cell.row


def by_column(pair: Tuple[CellPos, CellPos]) -> Label:
    """grouper for CellPos pairs. returns the col label of the original cell"""
    cell, _ = pair
    return cell.column


def by_result_cell(pair: Tuple[CellPos, CellPos]) -> LabelPair:
    """
    grouper for CellPos pairs. returns the row, col pair for resulting cell
    """
    _, cell = pair
    return cell.row, cell.column


def make_map_sets(pairs: Iterable[PosPair], key: Callable) -> List[Mark]:
    """groups pairs by key, then makes a map set for each group"""
    pairs = sorted(pairs, key=key)
    return [
        MapSet([Map(from_, to) for from_, to in g])
        for _, g in itertools.groupby(pairs, key=key)
    ]


##############################################################################
# debugging
##############################################################################


def print_cell_sets(val: List[MapSet]) -> None:
    """helper to print mapsets of CellPos"""
    for i, mapset in enumerate(val):
        print(f"{i}:")
        for map_mark in mapset.maps:
            left = (
                f"{str(map_mark.from_.row)}, "  # type: ignore
                f"{str(map_mark.from_.column)}"  # type: ignore
            )
            right = (
                f"{str(map_mark.to.row)}, "  # type: ignore
                f"{str(map_mark.to.column)}"  # type: ignore
            )
            print(f"  {left} -> {right}")


def print_axis_sets(val: List[MapSet]) -> None:
    """helper to print mapsets of AxisPos"""
    for i, mapset in enumerate(val):
        print(f"{i}:")
        for map_mark in mapset.maps:
            left = (
                f"({str(map_mark.from_.anchor)}) "  # type: ignore
                f"{str(map_mark.from_.label)}"  # type: ignore
            )
            right = (
                f"({str(map_mark.to.anchor)}) "  # type: ignore
                f"{str(map_mark.to.label)}"  # type: ignore
            )
            print(f"  {left} -> {right}")
