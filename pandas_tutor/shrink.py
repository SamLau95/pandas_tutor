"""
Remove rows to fit in RAM
"""
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

import pandas as pd

from pandas_tutor.run import (
    EvalResult,
)

from .diagram import (
    RuntimeErrorInChain,
)

from pandas_tutor import util

def shrink_memory(
    results: List[EvalResult], max_iterations: int = 5
) -> List[EvalResult]:
    """Checks the amount of memory being used in results.vals and shrinks them if need be.

    Args:
        results (List[EvalResult]): EvalResults comes from the run function
        max_iterations (int, optional): Describes to recursive function how many more times to iterate. Defaults to 5.

    Returns:
        List[EvalResult]: _description_
    """
    
    total_mem_used = sum(util.mem_used(result.val) for result in results)
    print(total_mem_used, util.MEM_LIMIT)
    if total_mem_used < util.MEM_LIMIT:
        return results
    if max_iterations == 0:
        result = results[-1]
        return [
            RuntimeErrorInChain(
                code_step=result.step.code,
                message=util.too_much_mem_msg(total_mem_used),
                fragment=result.fragment,
            )
        ]
    
    # remove rows if we have too much memory
    results = shrink(results, total_mem_used)
    
    print(total_mem_used, max_iterations)
    return shrink_memory(results, max_iterations - 1)

def shrink(results: List[EvalResult], total_mem_used: int) -> List[EvalResult]:
    # remove rows if we have too much memory
    # 
    
    target_mem = util.MEM_LIMIT * 0.9 
    reduction = total_mem_used / target_mem
    
    for result in results:
        if isinstance(result.val, pd.DataFrame):
            result.val = result.val.iloc[: int(len(result.val) // reduction)]
        elif isinstance(result.val, pd.Series):
            result.val = result.val.iloc[: int(len(result.val) // reduction)]
        elif isinstance(result.val, util.DataFrameGroupBy): 
            result.val = result.val.df.iloc[: int(len(result.val.df) // reduction)] # TODO: This doesn't work
        elif isinstance(result.val, util.SeriesGroupBy):
            result.val = result.val.series.iloc[: int(len(result.val.series) // reduction)]
        elif isinstance(result.val, pd.Index):
            result.val = result.val[: int(len(result.val) // reduction)]
        else:
            raise NotImplementedError(f"can't shrink {result}")
    return results