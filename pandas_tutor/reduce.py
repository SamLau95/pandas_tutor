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
    else: # don't know what to do, so just do nothing
        before_imp, after_imp = before, after

    before_main = grab_important(before_imp, before)
    after_main = grab_important(after_imp, after)

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


def grab_important(important_score: tuple, obj : t.Any):
    """return top MAX_ROWs based on importance as boolean index"""
    # grab top values
    # grab head & tail
    row_score = important_score[0]
    col_score = important_score[1]
    
    key_rows = [i[0] for i in sorted(row_score.items(), key= lambda item: item[1], reverse=True)[:MAX_ROWS]]
    if isinstance(obj, pd.DataFrame):
        # get the most important row and columns names
        key_columns = [i[0] for i in sorted(col_score.items(), key= lambda item: item[1], reverse=True)[:MAX_ROWS]]
        return key_rows, key_columns

    return key_rows


def final_filter(val: t.Any, limit: pd.Index) -> t.Any:
    """Return the final filtered value"""
    if isinstance(val, pd.DataFrame):
        return val.loc[limit]
    elif isinstance(val, pd.Series):
        return val.loc[limit]
    elif isinstance(val, pd.Index):
        return None # val[bool_index] 
    elif isinstance(
        val, util.DataFrameGroupBy
    ):  # might be wrong, I'm thinking val.obj[bool_index]
        return None #val.filter(bool_index)
    elif isinstance(val, util.SeriesGroupBy):  # might be wrong
        return None #val.filter(bool_index)
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
    # find shared cols

    get_call = eval(step.labels_expr)
    get_col = [get_call] if isinstance(get_call, str) else get_call


    if isinstance(before, pd.DataFrame) and isinstance(after, pd.DataFrame):
        # initialize importance metric through dictionary
        befo_main_row = initialize_index_score(before)
        befo_main_col = initialize_col_score(before)
        afte_main_row = initialize_index_score(after)
        afte_main_col = initialize_col_score(after)


        # increase their priortiy score
        improve_priority(befo_main_col, get_col)
        improve_priority(afte_main_col, get_col)

        return ((befo_main_row, befo_main_col), (afte_main_row, afte_main_col))

    elif isinstance(before, pd.Series) and isinstance(after, pd.Series):
        befo_main_row = initialize_index_score(before)
        afte_main_row = initialize_index_score(after)

        return ((befo_main_row, None), (afte_main_row, None))
    elif isinstance(before, pd.DataFrame) and isinstance(after, pd.Series):
        befo_main_row = initialize_index_score(before)
        befo_main_col = initialize_col_score(before)

        afte_main_row = initialize_index_score(after)
        return ((befo_main_row, befo_main_col), (afte_main_row, None))
    else:
        return ((None, None), (None, None))

def initialize_index_score(obj : t.Union[pd.DataFrame, pd.Series]) -> dict:
    default_index_score = np.zeros(len(obj.index))
    default_index_score[:HEAD_COUNTS] = 1
    default_index_score[-TAIL_COUNTS:] = 1

    return {index: score for index, score in zip(obj.index, default_index_score)}

def initialize_col_score(obj : t.Union[pd.DataFrame, pd.Series]) -> dict:
    default_col_score = np.zeros(len(obj.columns))
    default_col_score[:HEAD_COUNTS] = 1
    default_col_score[-TAIL_COUNTS:] = 1

    return {index: score for index, score in zip(obj.columns, default_col_score)}



def improve_priority(score : dict, improve_eles : t.Any) -> None:
    for ele in improve_eles:
        score[ele] += 1