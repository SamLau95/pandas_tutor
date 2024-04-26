"""
Remove rows to fit in RAM
"""

import pandas as pd
import typing as t

from pandas_tutor.run import (
    EvalResult,
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


def reduce_memory(before: t.Any, after: t.Any, step: ChainStep):

    if assess_small(before) and assess_small(after):
        return before, after

    # Decide how many rows we want at the top and bottom
    head_size = MAX_ROWS // 10

    # LOGIC HERE
    # initialize before & after importance for type hinting

    if isinstance(step, EvalError):
        ...  # handle error
    elif isinstance(step, PassThroughCall):
        ...  # handle passthrough
    elif isinstance(step, GetCall):
        before_imp, after_imp = reduce_for_get(before, after, step)
    ...

    before_bool = grab_important(before_imp)
    after_bool = grab_important(after_imp)

    # Indicate the rows you want to keep from after.val because before.val was already ripped from?
    # Gonna need some flag to indicate that it's the first in the chain and to edit the LHS
    # if isinstance(step, HeadCall):
    #     before = before.head(1)
    #     after = after.head(1)

    return final_filter(before, before_bool), final_filter(after, after_bool)


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


def grab_important(importance_index: pd.Index) -> pd.Index:
    """return top MAX_ROWs based on importance as boolean index"""
    # grab top values
    # grab head & tail
    return ...


def grab_head_tail(val: t.Any) -> pd.Series:
    return


def final_filter(val: t.Any, bool_index: pd.Index) -> t.Any:
    """Return the final filtered value"""
    if isinstance(val, pd.DataFrame):
        return val[bool_index]
    elif isinstance(val, pd.Series):
        return val[bool_index]
    elif isinstance(val, pd.Index):
        return val[bool_index]
    elif isinstance(
        val, util.DataFrameGroupBy
    ):  # might be wrong, I'm thinking val.obj[bool_index]
        return val.filter(bool_index)
    elif isinstance(val, util.SeriesGroupBy):  # might be wrong
        return val.filter(bool_index)
    else:
        return NotImplementedError(
            f"Type {type(val)} not implemented in final_filter"
        )


# df.get(['Name'])
def reduce_for_get(
    before: t.Any, after: t.Any, step: GetCall
) -> t.Tuple[pd.Index, pd.Index]:
    """Return an importance score for each row"""
    # Logic to rank the importance of each row

    return
