"""
Remove rows to fit in RAM
"""

import pandas as pd
import typing as t
import numpy as np
import dataclasses

from pandas_tutor.run import (
    Arg,
    DFResult,
    EvalResult,
    GroupbyResult,
    ScalarResult,
    SeriesGroupbyResult,
    SeriesResult,
)

from .diagram import (
    RuntimeErrorInChain,
)

from pandas_tutor import util

from typing import List

from pandas_tutor.parse_nodes import (
    GroupByAggCall,
    ApplyCall,
    AssignCall,
    BoolExprStep,
    ChainStep,
    DropCall,
    EvalError,
    GetCall,
    GroupByCall,
    GroupByFilterCall,
    HeadCall,
    JoinCall,
    MeltCall,
    MergeCall,
    PassThroughCall,
    PivotCall,
    PivotTableCall,
    RenameCall,
    ResetIndexCall,
    SetIndexCall,
    SortValuesCall,
    StackCall,
    SubsComparison,
    Subscript,
    SubscriptEl,
    TailCall,
    UnstackCall,
)

MAX_ROWS = 100
HEAD_COUNTS = 5
TAIL_COUNTS = 5


@dataclasses.dataclass
class ImportanceMatrix:
    rows: np.array
    cols: np.array


def reduce_memory(before: t.Any, after: t.Any, step: ChainStep):
    # Decide how many rows we want at the top and bottom
    head_size = MAX_ROWS // 10

    if assess_small(before) and assess_small(after):
        return before, after

    # based on the step kind
    # assign importance score to both row and col
    before_imp: ImportanceMatrix
    after_imp: ImportanceMatrix

    if isinstance(step, EvalError):
        ...  # TODO: handle error
    elif isinstance(step, PassThroughCall):
        ...  # TODO: handle passthrough
    elif isinstance(step, GetCall):
        before_imp, after_imp = reduce_for_get(before, after, step)
    elif isinstance(step, SortValuesCall):
        before_imp, after_imp = reduce_for_sort_values(before, after, step)
    # elif isinstance(step, DropCall):
    #     before_imp, after_imp = reduce_for_drop(before, after, step)
    # elif isinstance(step, RenameCall):
    #     before_imp, after_imp = reduce_for_rename(before, after, step)
    # elif isinstance(step, HeadCall) or isinstance(step, TailCall):
    #     before_imp, after_imp = reduce_for_head_or_tail(before, after, step)
    # elif isinstance(step, ApplyCall):
    #     before_imp, after_imp = reduce_for_apply(before, after, step)
    # elif isinstance(step, AssignCall):
    #     before_imp, after_imp = reduce_for_assign(before, after, step)
    # elif isinstance(step, GroupByCall):
    #     before_imp, after_imp = reduce_for_groupby(before, after, step)
    # elif isinstance(step, GroupByAggCall):
    #     before_imp, after_imp = reduce_for_agg(before, after, step)
    # elif isinstance(step, GroupByFilterCall):
    #     before_imp, after_imp = reduce_for_groupby_filter(before, after, step)
    # elif isinstance(step, ResetIndexCall):
    #     before_imp, after_imp = reduce_for_reset_index(before, after, step)
    # elif isinstance(step, SetIndexCall):
    #     before_imp, after_imp = reduce_for_set_index(before, after, step)
    # elif isinstance(step, UnstackCall):
    #     before_imp, after_imp = reduce_for_unstack(before, after, step)
    # elif isinstance(step, StackCall):
    #     before_imp, after_imp = reduce_for_stack(before, after, step)
    # elif isinstance(step, PivotCall):
    #     before_imp, after_imp = reduce_for_pivot(before, after, step)
    # elif isinstance(step, PivotTableCall):
    #     before_imp, after_imp = reduce_for_pivot_table(before, after, step)
    # elif isinstance(step, MeltCall):
    #     before_imp, after_imp = reduce_for_melt(before, after, step)
    # elif isinstance(step, MergeCall):
    #     before_imp, after_imp = reduce_for_merge(before, after, step)
    # elif isinstance(step, JoinCall):
    #     before_imp, after_imp = reduce_for_join(before, after, step)
    # elif isinstance(step, BoolExprStep):
    #     before_imp, after_imp = reduce_for_bool_expr(before, after, step)
    # elif isinstance(step, Subscript):
    #     before_imp, after_imp = reduce_for_subscript(before, after, step)
    else:  # TODO: handle other cases
        return before, after

    before_main = priority_pos(before_imp)
    after_main = priority_pos(after_imp)

    # Indicate the rows you want to keep from after.val because before.val was already ripped from?
    # Gonna need some flag to indicate that it's the first in the chain and to edit the LHS
    # if isinstance(step, HeadCall):
    #     before = before.head(1)
    #     after = after.head(1)

    return final_filter(before, before_main), final_filter(after, after_main)


def assess_small(val: t.Any) -> bool:
    """Assess if value should be reduced"""
    if isinstance(val, pd.DataFrame):
        return len(val) < MAX_ROWS and len(val.columns) < MAX_ROWS
    elif isinstance(val, pd.Series):
        return len(val) < MAX_ROWS
    elif isinstance(val, pd.Index):
        # Chris doesn't know exactly when Index occurs
        return len(val) < MAX_ROWS
    elif isinstance(val, util.DataFrameGroupBy):
        return val.size().sum() < MAX_ROWS and val.obj.shape[1] < MAX_ROWS
    elif isinstance(val, util.SeriesGroupBy):
        return val.size().sum() < MAX_ROWS
    else:
        return NotImplementedError(
            f"Type {type(val)} not implemented in assess_small"
        )


def final_filter(val: t.Any, limit: np.array) -> t.Any:
    """Return the final filtered value"""
    if isinstance(val, pd.DataFrame):
        breakpoint()
        return val.iloc[limit[0], limit[1]]
    elif isinstance(val, pd.Series):
        breakpoint()
        return val.iloc[limit[0]]
    elif isinstance(val, pd.Index):
        return None  # val[bool_index]
    elif isinstance(val, util.DataFrameGroupBy):
        # might be wrong, I'm thinking val.obj[bool_index]
        return None  # val.filter(bool_index)
    elif isinstance(val, util.SeriesGroupBy):  # might be wrong
        return None  # val.filter(bool_index)
    else:
        return NotImplementedError(
            f"Type {type(val)} not implemented in final_filter"
        )


### Importance Matrix Functions ###


def initialize_matrix(val: t.Any) -> ImportanceMatrix:
    # TODO: put the type-checking in here.
    row: int
    col: t.Union[int, None]

    if isinstance(val, pd.DataFrame):
        row, col = val.shape
    elif isinstance(val, pd.Series):
        row = len(val)
        col = None
    elif isinstance(val, pd.Index):
        row = len(val)
        col = None
    elif isinstance(val, util.DataFrameGroupBy):
        row, col = val.obj.shape
    elif isinstance(val, util.SeriesGroupBy):
        row = len(val.obj)
        col = None
    else:
        return NotImplementedError(
            f"Type {type(val)} not implemented in initialize_matrix"
        )

    col_matrix = col
    if col != None:
        col_matrix = np.zeros(col)
        col_matrix[:HEAD_COUNTS] = 1
        col_matrix[-TAIL_COUNTS:] = 1

    row_matrix = np.zeros(row)
    row_matrix[:HEAD_COUNTS] = 1
    row_matrix[-TAIL_COUNTS:] = 1

    return ImportanceMatrix(row_matrix, col_matrix)


def improve_priority(matrix: np.array, improve_pos: np.array) -> None:
    # This could be a class function for ImportanceMatrix
    matrix[improve_pos] += 1


def get_position(
    obj: t.Union[pd.DataFrame, pd.Series], vals: List[str], index: bool
):
    if isinstance(obj, pd.DataFrame):
        if index:
            return [obj.index.get_loc(val) for val in vals]
        return [obj.columns.get_loc(val) for val in vals]
    return [obj.index.get_loc(val) for val in vals]


def priority_pos(imp_matrix: ImportanceMatrix) -> List[int]:
    positions = []
    for dim in dataclasses.astuple(imp_matrix):
        if dim is not None:
            priority_matrix = sorted(
                enumerate(dim), key=lambda ele: ele[1], reverse=True
            )[:MAX_ROWS]
            priority_index = [val[0] for val in priority_matrix]
            positions.append(sorted(priority_index))
        else:
            positions.append(None)

    return positions


### Reduce Functions ###


# df.get(['Name'])
# df.get('Name')
# df.get(['Name1', 'Name2'])
def reduce_for_get(
    before: t.Any, after: t.Any, step: GetCall
) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]:
    """
    take in

    Return an importance score for each row

    """
    # initialize importance matrix
    before_matrix = initialize_matrix(before)
    after_matrix = initialize_matrix(after)

    # find the column called by the get method
    get_call = eval(step.labels_expr)
    share_col = [get_call] if isinstance(get_call, str) else get_call

    if isinstance(before, pd.DataFrame) and isinstance(after, pd.DataFrame):
        improve_priority(
            after_matrix.cols, get_position(after, share_col, False)
        )
        improve_priority(
            before_matrix.cols, get_position(before, share_col, False)
        )

    elif isinstance(before, pd.Series) and isinstance(after, pd.Series):
        pass  # do nothing

    elif isinstance(before, pd.DataFrame) and isinstance(after, pd.Series):

        # increase the importance score of the before dataframe
        improve_priority(
            before_matrix.cols, get_position(before, share_col, False)
        )

    return before_matrix, after_matrix


# df.sort_values('Name')
def reduce_for_sort_values(
    before: t.Any, after: t.Any, step: GetCall
) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]:

    # Handle error
    if not (
        isinstance(before, (pd.DataFrame, pd.Series))
        and isinstance(after, (pd.DataFrame, pd.Series))
    ):
        return [], []  # TODO: handle error

    # Initialize importance matrices
    before_matrix = initialize_matrix(before)
    after_matrix = initialize_matrix(after)

    sort_by = (
        eval(step.label_expr)
        if isinstance(step.label_expr, str)
        else step.label_expr
    )
    if isinstance(sort_by, str):
        sort_by = [sort_by]

    # Handle columns of DataFrames
    if isinstance(before, pd.DataFrame) and isinstance(after, pd.DataFrame):
        improve_priority(
            before_matrix.cols, get_position(before, sort_by, False)
        )
        improve_priority(after_matrix.cols, get_position(after, sort_by, False))

    # prioritize rows of dataframes in before and after
    rows_to_grab = MAX_ROWS - HEAD_COUNTS - TAIL_COUNTS
    from_top = rows_to_grab // 2
    from_bottom = rows_to_grab - from_top

    top_bottom = after[:from_top].index.append(after[-from_bottom:].index)
    improve_priority(before_matrix.rows, get_position(before, top_bottom, True))
    improve_priority(after_matrix.rows, get_position(after, top_bottom, True))

    return before_matrix, after_matrix


# def reduce_for_drop(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_rename(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_head_or_tail(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_apply(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_assign(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_groupby(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_agg(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_groupby_filter(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_reset_index(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_set_index(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_unstack(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_stack(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_pivot(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_pivot_table(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_melt(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_merge(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_join(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_bool_expr(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...


# def reduce_for_subscript(
#     before: t.Any, after: t.Any, step: GetCall
# ) -> t.Tuple[ImportanceMatrix, ImportanceMatrix]: ...
