'''
executes parsed python code to compute the intermediate values within the
last line of the code.
'''

from __future__ import annotations

import builtins
import dataclasses
import types
import typing as t

import pandas as pd

from . import util
from .parse_nodes import (AggCall, ChainStatement, ChainStep, EvalError,
                          ParsedModule, PassThroughCall, RawCode, Subscript)

# technically args can be anything...but most of the time it'll be labels
Arg = t.Union[str, t.List[str]]

Args = t.Dict[str, Arg]

# errors that we care about showing to the user
serializable_errors = (ArithmeticError, AttributeError, ImportError,
                       LookupError, NameError, RuntimeError, TypeError,
                       ValueError)


@dataclasses.dataclass
class EvalBase:
    step: ChainStep
    args: Args


@dataclasses.dataclass
class DFResult(EvalBase):
    val: pd.DataFrame


@dataclasses.dataclass
class SeriesResult(EvalBase):
    val: pd.Series


@dataclasses.dataclass
class GroupbyResult(EvalBase):
    val: util.DataFrameGroupBy


@dataclasses.dataclass
class SeriesGroupbyResult(EvalBase):
    val: util.SeriesGroupBy


@dataclasses.dataclass
class ImageResult(EvalBase):
    val: t.Any


@dataclasses.dataclass
class RuntimeErrorResult(EvalBase):
    val: Exception


@dataclasses.dataclass
class UnhandledResult(EvalBase):
    '''catch-all for chain outputs we don't know how to serialize'''
    val: t.Any


EvalResult = t.Union[UnhandledResult, DFResult, SeriesResult, GroupbyResult,
                     SeriesGroupbyResult, ImageResult, RuntimeErrorResult]


# TODO: handle stdout and stderr from user code
def run(root: ParsedModule) -> t.List[EvalResult]:
    statements = root.statements

    # hard-code the last one!
    setup_stmts, last_expr = statements[:-1], statements[-1]
    if not isinstance(last_expr, ChainStatement):
        # don't visualize
        return []

    # all the code above the last expression
    setup_code = RawCode('\n'.join([stmt.code for stmt in setup_stmts]))

    # now let's run stuff dangerously!
    user_globals = setup_user_globals()

    try:
        exec(setup_code, user_globals)
    except serializable_errors as error:
        step = EvalError.from_code(setup_code)
        return [RuntimeErrorResult(step=step, args={}, val=error)]

    last_val: t.Any = None
    eval_results: t.List[EvalResult] = []
    for step in last_expr.chain:
        try:
            # wrap individual steps in parens before eval since subexpressions
            # within a line can have newlines
            val = eval(f"({step.code})", user_globals)
            args = eval_args(step, user_globals)
        except serializable_errors as error:
            step = EvalError.from_code(step.code)
            err_result = RuntimeErrorResult(step=step, args={}, val=error)
            eval_results.append(err_result)
            break

        result = make_result(step, val, args, last_val)
        eval_results.append(result)
        last_val = val

    return eval_results


# need the last_val for the special case where we have an agg that doesn't show
# up immediately after a groupby, like dogs.groupby(...)['...'].mean().
def make_result(step: ChainStep, val: t.Any, args: Args,
                last_val: t.Any) -> EvalResult:
    if (isinstance(step, PassThroughCall)
            and isinstance(last_val,
                           (util.DataFrameGroupBy, util.SeriesGroupBy))
            and isinstance(val, (pd.DataFrame, pd.Series))):
        step = AggCall.from_passthrough_call(step)

    if isinstance(val, util.DataFrameGroupBy):
        return GroupbyResult(step, args, val)
    elif isinstance(val, util.SeriesGroupBy):
        return SeriesGroupbyResult(step, args, val)
    elif isinstance(val, pd.DataFrame):
        return DFResult(step, args, val)
    elif isinstance(val, pd.Series):
        return SeriesResult(step, args, val)
    elif util.is_plottable(val):
        return ImageResult(step, args, val)
    else:
        return UnhandledResult(step, args, val)


def setup_user_globals():
    # set up scope like PythonTutor
    user_builtins = {}
    assert isinstance(builtins, types.ModuleType)
    for k in dir(builtins):
        user_builtins[k] = getattr(builtins, k)

    user_globals = {}

    user_globals.update({
        "__name__": "__main__",
        "__builtins__": user_builtins
    })

    return user_globals


def eval_args(step: ChainStep, user_globals: dict) -> Args:
    '''eval each arg marked with parse_nodes.evals_into()'''
    if isinstance(step, Subscript):
        return eval_args_subscript(step, user_globals)
    return eval_dataclass(step, user_globals)


def eval_args_subscript(step: Subscript, user_globals: dict) -> Args:
    '''subscripts have nested eval exprs so we have a special case'''
    slice1_args = eval_dataclass(step.slice1, user_globals, attr='slice1')
    slice2_args = eval_dataclass(step.slice2, user_globals, attr='slice2')
    return {**slice1_args, **slice2_args}


def eval_dataclass(obj: t.Any, user_globals: dict, attr='') -> Args:
    '''
    takes a dataclasss with fields marked by evals_into(), outputs
    dict of evaluated values
    '''
    args: Args = {}
    if obj is None:
        return args

    fields = [
        field for field in dataclasses.fields(obj)
        if field.metadata.get('evals_into', False)
    ]

    for field in fields:
        evals_into = field.metadata['evals_into'].format(attr=attr)
        to_eval: t.Union[RawCode, t.List[RawCode]] = getattr(obj, field.name)
        if isinstance(to_eval, list):
            result = [eval(f"({code})", user_globals) for code in to_eval]
        else:
            result = eval(f"({to_eval})", user_globals)
        args[evals_into] = result
    return args
