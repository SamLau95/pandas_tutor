"""
Remove rows to fit in RAM
"""

import pandas as pd
import typing as t
import numpy as np

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


def reduce_memory(before: t.Any, after: t.Any, step: ChainStep):
    # Decide how many rows we want at the top and bottom
    head_size = MAX_ROWS // 10

    if assess_small(before) and assess_small(after):
        return before, after

    # based on the step kind
    # assign importance score to both row and col
    if isinstance(step, EvalError):
        ...  # handle error
    elif isinstance(step, PassThroughCall):
        ...  # handle passthrough
    elif isinstance(step, GetCall):
        before_imp, after_imp = reduce_for_get(before, after, step)
    else:  # don't know what to do, so just do nothing
        before_imp, after_imp = before, after

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
    elif isinstance(
        val, pd.Index
    ):  # Chris doesn't know exactly when Index occurs
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
    elif isinstance(
        val, util.DataFrameGroupBy
    ):  # might be wrong, I'm thinking val.obj[bool_index]
        return None  # val.filter(bool_index)
    elif isinstance(val, util.SeriesGroupBy):  # might be wrong
        return None  # val.filter(bool_index)
    else:
        return NotImplementedError(
            f"Type {type(val)} not implemented in final_filter"
        )


# df.get(['Name'])
# df.get('Name')
# df.get(['Name1', 'Name2'])
def reduce_for_get(
    before: t.Any, after: t.Any, step: GetCall
) -> t.Tuple[pd.Index, pd.Index]:
    """
    take in

    Return an importance score for each row

    """
    # initialize importance metrics
    # the metric is going be an nested array of len 2
    before_matrix = (
        initialize_matrix(*before.shape)
        if isinstance(before, pd.DataFrame)
        else initialize_matrix(len(before), None)
    )
    after_matrix = (
        initialize_matrix(*after.shape)
        if isinstance(after, pd.DataFrame)
        else initialize_matrix(len(after), None)
    )

    # find the column called by the get method
    get_call = eval(step.labels_expr)
    share_col = [get_call] if isinstance(get_call, str) else get_call

    if isinstance(before, pd.DataFrame) and isinstance(after, pd.DataFrame):
        improve_priority(after_matrix[1], get_position(after, share_col, False))
        improve_priority(
            before_matrix[1], get_position(before, share_col, False)
        )

    elif isinstance(before, pd.Series) and isinstance(after, pd.Series):
        pass  # do nothing

    elif isinstance(before, pd.DataFrame) and isinstance(after, pd.Series):

        # increase the importance score of the before dataframe
        improve_priority(
            before_matrix[1], get_position(before, share_col, False)
        )

    return before_matrix, after_matrix


def initialize_matrix(row, col):
    col_metric = col
    if col != None:
        col_metric = np.zeros(col)
        col_metric[:HEAD_COUNTS] = 1
        col_metric[-TAIL_COUNTS:] = 1
    row_metric = np.zeros(row)
    row_metric[:HEAD_COUNTS] = 1
    row_metric[-TAIL_COUNTS:] = 1
    return (row_metric, col_metric)


def improve_priority(metric: np.array, improve_pos: np.array) -> None:
    metric[improve_pos] += 1


def get_position(obj: t.Union[pd.DataFrame, pd.Series], vals, index: bool):
    if isinstance(obj, pd.DataFrame):
        if index:
            return [obj.index.get_loc(val) for val in vals]
        return [obj.columns.get_loc(val) for val in vals]
    return [obj.index.get_loc(val) for val in vals]


def priority_pos(metrics: np.array):
    positions = []
    for metric in metrics:
        if metric is not None:
            priority_metric = sorted(
                enumerate(metric), key=lambda ele: ele[1], reverse=True
            )[:MAX_ROWS]
            priortiy_index = [val[0] for val in priority_metric]
            positions.append(sorted(priortiy_index))
        else:
            positions.append(None)

    return positions
