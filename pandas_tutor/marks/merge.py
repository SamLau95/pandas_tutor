"""marks for join operations, like merge() and join()"""

from typing import List, Optional, Sequence, Tuple, Union, cast

import pandas as pd
from pandas_tutor import util
from pandas_tutor.diagram import AxisPos, Mark, PosPair, Using
from pandas_tutor.marks.mark_utils import (  # noqa: F401
    lhs,
    lhs2,
    lhs2_index,
    lhs2_series,
    lhs_index,
    lhs_series,
    make_drops,
    make_map_sets,
    make_usings,
    print_axis_sets,
    rhs,
    rhs_index,
)
from pandas_tutor.parse_nodes import JoinCall, MergeCall
from pandas_tutor.run import Args, DFResult, EvalResult, SeriesResult
from pandas_tutor.util import Label


def mark_for_merge(
    step: MergeCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    # there's no Series.merge() method, but pd.merge(left, right) can take a
    # series as the left arg
    if not (
        isinstance(before, (DFResult, SeriesResult))
        and isinstance(after, DFResult)
    ):
        return []

    left = before.val
    right = after.val
    args = after.args
    left2 = args.get("right")

    how: str = cast(str, args.get("how", "inner"))
    on_orig = args.get("on")
    left_on_orig = args.get("left_on")
    right_on_orig = args.get("right_on")
    left_index: bool = cast(bool, args.get("left_index", False))
    right_index: bool = cast(bool, args.get("right_index", False))

    # sort=False as default is important to match behavior of pd.merge() since
    # get_join_info() has sort=True
    sort: bool = cast(bool, args.get("sort", False))

    if not util.is_pd(left2):
        return []

    return _merge_marks(
        left,
        left2,
        right,
        how=how,
        on_orig=on_orig,
        left_on_orig=left_on_orig,
        right_on_orig=right_on_orig,
        left_index=left_index,
        right_index=right_index,
        sort=sort,
    )


def mark_for_join(
    step: JoinCall, before: EvalResult, after: EvalResult
) -> List[Mark]:
    if not (isinstance(before, DFResult) and isinstance(after, DFResult)):
        return []

    left = before.val
    right = after.val
    args = after.args
    left2 = args.get("other")

    # note that .join() uses a *left join* by default, not inner
    how: str = cast(str, args.get("how", "left"))
    on_orig = args.get("on")

    # sort=False as default is important to match behavior of pd.join() since
    # get_join_info() has sort=True
    sort: bool = cast(bool, args.get("sort", False))

    # .join() can technically take a *list* of dataframes to join with, but we
    # only handle the single dataframe case
    if not util.is_pd(left2):
        return []

    # recreate pandas join() logic from pd.Dataframe._join_compat()

    if how == "cross":
        return _merge_marks(
            left, left2, right, how=how, on_orig=on_orig, sort=sort
        )

    return _merge_marks(
        left,
        left2,
        right,
        how=how,
        left_on_orig=on_orig,
        left_index=on_orig is None,
        right_index=True,
        sort=sort,
    )


def _merge_marks(
    left_orig: Union[pd.DataFrame, pd.Series],
    left2_orig: Union[pd.DataFrame, pd.Series],
    right: pd.DataFrame,
    how: str = "inner",
    on_orig: Union[Label, Sequence[Label], None] = None,
    left_on_orig: Union[Label, Sequence[Label], None] = None,
    right_on_orig: Union[Label, Sequence[Label], None] = None,
    left_index: bool = False,
    right_index: bool = False,
    sort: bool = False,
) -> List[Mark]:
    """
    used to make marks for all merge methods
    """
    left_is_series = isinstance(left_orig, pd.Series)
    left: pd.DataFrame = left_orig.to_frame() if left_is_series else left_orig

    left2_is_series = isinstance(left2_orig, pd.Series)
    left2: pd.DataFrame = (
        left2_orig.to_frame() if left2_is_series else left2_orig
    )

    on = util.listify(on_orig) if on_orig else None
    left_on = (
        on if on_orig else util.listify(left_on_orig) if left_on_orig else None
    )
    right_on = (
        on
        if on_orig
        else util.listify(right_on_orig)
        if right_on_orig
        else None
    )

    if not (on or left_on or right_on or left_index or right_index):
        # default on= is intersection of columns
        on = left_on = right_on = list(left.columns.intersection(left2.columns))

    # don't handle cases where we join using both index and columns since that
    # creates duplicate index labels
    if left_index is not right_index:
        return []

    res_index, left_row_nums, left2_row_nums = util.get_join_info(
        left=left_orig,
        right=left2_orig,
        how=how,
        on=on_orig,
        left_on=left_on_orig,
        right_on=right_on_orig,
        left_index=left_index,
        right_index=right_index,
        sort=sort,
    )
    # a left join on the indexes keeps the same index as the left df, and
    # pandas sets left_row_nums=None.
    if left_row_nums is None:
        left_row_nums = pd.RangeIndex(len(left))
    # same deal for right joins
    if left2_row_nums is None:
        left2_row_nums = pd.RangeIndex(len(left2))

    # mark all columns used for joining
    if left_on and right_on:
        left_on = cast(List, left_on)  # keep mypy happy
        right_on = cast(List, right_on)

        # special case to handle series
        lhs_usings = (
            make_usings(left_on, "column", "lhs")
            if not left_is_series
            else [Using(lhs_series())]
        )

        lhs2_usings = (
            make_usings(right_on, "column", "lhs2")
            if not left2_is_series
            else [Using(lhs2_series())]
        )

        using = [
            *lhs_usings,
            *lhs2_usings,
            *make_usings(on if on else left_on + right_on, "column", "rhs"),
        ]
    else:  # we're joining on the indexes
        using = cast(
            List[Mark],
            [Using(lhs_index("row", i)) for i in range(left.index.nlevels)]
            + [Using(lhs2_index("row", i)) for i in range(left2.index.nlevels)]
            + [Using(rhs_index("row", i)) for i in range(right.index.nlevels)],
        )

    # mark all rows dropped from either lhs or lhs2
    drops = [
        *make_drops(_dropped_labels(left.index, left_row_nums), "row", "lhs"),
        *make_drops(
            _dropped_labels(left2.index, left2_row_nums), "row", "lhs2"
        ),
    ]

    def row_pairs(left_num: int, left2_num: int, right_row: Label):
        left_row = cast(Label, left.index[left_num])
        left2_row = cast(Label, left2.index[left2_num])
        if left_num != -1:
            yield (lhs("row", left_row), rhs("row", right_row))
        if left2_num != -1:
            yield (lhs2("row", left2_row), rhs("row", right_row))
        # don't actually need this last case since if lhs -> rhs and lhs2 ->
        # rhs, we automatically have lhs and lhs2 in mapset together
        # if left_num != -1 and left2_num != -1:
        #     yield (lhs("row", left_row), lhs2("row", left2_row))

    pairs: List[PosPair] = [
        pair
        for left_num, left2_num, right_row in zip(
            left_row_nums, left2_row_nums, res_index
        )
        for pair in row_pairs(left_num, left2_num, right_row)
    ]

    # the merge key is a tuple of row values or an index label from lhs or lhs2
    def by_merge_key(pair: Tuple[AxisPos, AxisPos]):
        # pair is always {lhs, lhs2} -> rhs
        pos, _ = pair
        df = left if pos.anchor == "lhs" else left2
        key = left_on if pos.anchor == "lhs" else right_on

        # BUG: this breaks when the merge keys have index level names!
        # https://github.com/SamLau95/pandas_tutor/issues/154
        row = df.loc[pos.label]
        # if pos.label is duplicated, row is a dataframe
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        return tuple(row.loc[key]) if key else row.name

    row_sets = make_map_sets(pairs, key=by_merge_key)

    # print_axis_sets(row_sets)
    # breakpoint()

    return [*using, *drops, *row_sets]


def _get_left2_arg(args: Args) -> Tuple[Optional[pd.DataFrame], bool]:
    left2_arg = args.get("right")

    # merge with a series treats the series as a 1-column dataframe
    if isinstance(left2_arg, pd.Series):
        return (left2_arg.to_frame(), True)
    return (left2_arg if isinstance(left2_arg, pd.DataFrame) else None, False)


def _dropped_labels(index: pd.Index, row_nums: pd.Index) -> pd.Index:
    dropped = pd.RangeIndex(len(index)).difference(row_nums)
    return index[dropped]
