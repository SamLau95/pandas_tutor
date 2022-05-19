"""
executes parsed python code to compute the intermediate values within the
last line of the code.
"""

from __future__ import annotations

import builtins
import contextlib
import dataclasses
import sys
import types
import typing as t

import pandas as pd

from . import util
from .parse_nodes import (
    AggCall,
    ChainStatement,
    ChainStep,
    CodeRange,
    EvalError,
    ParseResult,
    ParseSyntaxError,
    PassThroughCall,
    RawCode,
    Subscript,
)

# technically args can be anything...but most of the time it'll be labels
Arg = t.Union[str, list]

Args = t.Dict[str, Arg]


@dataclasses.dataclass
class EvalResult:
    step: ChainStep
    # location of fragment to highlight, relative to the entire expression
    fragment: CodeRange
    args: Args
    val: t.Any


@dataclasses.dataclass
class DFResult(EvalResult):
    val: pd.DataFrame


@dataclasses.dataclass
class SeriesResult(EvalResult):
    val: pd.Series


@dataclasses.dataclass
class GroupbyResult(EvalResult):
    val: util.DataFrameGroupBy


@dataclasses.dataclass
class SeriesGroupbyResult(EvalResult):
    val: util.SeriesGroupBy


@dataclasses.dataclass
class ImageResult(EvalResult):
    val: t.Any


@dataclasses.dataclass
class SyntaxErrorResult(EvalResult):
    step: ParseSyntaxError
    val: None


@dataclasses.dataclass
class RuntimeErrorResult(EvalResult):
    val: Exception


@dataclasses.dataclass
class UnhandledResult(EvalResult):
    """catch-all for chain outputs we don't know how to serialize"""

    val: t.Any


def run(root: ParseResult, ipython_shell=None) -> t.List[EvalResult]:
    """
    runs parsed code. in ipython, we pass in the shell object so we can
    run user code in their namespace.
    """
    # since we send JSON to stdout, we'll send user code's stdout to stderr.
    with contextlib.redirect_stdout(sys.stderr):
        return run_code(root, ipython_shell)


def run_code(root: ParseResult, ipython_shell=None) -> t.List[EvalResult]:
    if isinstance(root, ParseSyntaxError):
        return [
            SyntaxErrorResult(
                step=root, fragment=root.location, args={}, val=None
            )
        ]

    statements = root.statements

    # hard-code the last one!
    setup_stmts, last_expr = statements[:-1], statements[-1]

    # TODO: return warning when last statement isn't a chain
    if not isinstance(last_expr, ChainStatement):
        return []

    # grab user local vars from ipython shell if possible, otherwise initialize
    # a new globals dict
    user_globals = (
        setup_user_globals() if ipython_shell is None else ipython_shell.user_ns
    )

    for stmt in setup_stmts:
        try:
            exec(stmt.code, user_globals)
        except Exception as error:
            step = EvalError.from_node(stmt)
            return [
                RuntimeErrorResult(
                    step=step,
                    fragment=step.location,
                    args={},
                    val=error,
                )
            ]

    relative_to = last_expr.location.start
    last_val: t.Any = None
    eval_results: t.List[EvalResult] = []
    for step in last_expr.chain:
        fragment = step.location % relative_to

        try:
            # wrap individual steps in parens before eval since subexpressions
            # within a line can have newlines
            val = eval(f"({step.code})", user_globals)
            args = eval_args(step, user_globals)
        except Exception as error:
            step = EvalError.from_node(step)
            err_result = RuntimeErrorResult(
                step=step,
                fragment=fragment,
                args={},
                val=error,
            )
            eval_results.append(err_result)
            break

        result = make_result(step, fragment, args, val, last_val)
        eval_results.append(result)
        last_val = val

    # HACK: hard-code all step code strings to the entire statement's code
    # string to make fragment positions work. the code string for individual
    # function calls omits the whitespace that the fragment positions already
    # take into account.
    # https://github.com/SamLau95/pandas_tutor/issues/42
    for result in eval_results:
        result.step.code = last_expr.code
    return eval_results


# need the last_val for the special case where we have an agg that doesn't show
# up immediately after a groupby, like dogs.groupby(...)['...'].mean().
def make_result(
    step: ChainStep,
    fragment: CodeRange,
    args: Args,
    val: t.Any,
    last_val: t.Any,
) -> EvalResult:
    if (
        isinstance(step, PassThroughCall)
        and isinstance(last_val, (util.DataFrameGroupBy, util.SeriesGroupBy))
        and isinstance(val, (pd.DataFrame, pd.Series))
    ):
        step = AggCall.from_passthrough_call(step)

    if isinstance(val, util.DataFrameGroupBy):
        return GroupbyResult(step, fragment, args, val)
    elif isinstance(val, util.SeriesGroupBy):
        return SeriesGroupbyResult(step, fragment, args, val)
    elif isinstance(val, pd.DataFrame):
        return DFResult(step, fragment, args, val)
    elif isinstance(val, pd.Series):
        return SeriesResult(step, fragment, args, val)
    elif util.is_plottable(val):
        return ImageResult(step, fragment, args, val)
    else:
        return UnhandledResult(step, fragment, args, val)


def setup_user_globals():
    # set up scope like PythonTutor
    user_builtins = {}
    assert isinstance(builtins, types.ModuleType)
    for k in dir(builtins):
        user_builtins[k] = getattr(builtins, k)

    user_globals = {}

    user_globals.update({"__name__": "__main__", "__builtins__": user_builtins})

    return user_globals


def eval_args(step: ChainStep, user_globals: dict) -> Args:
    """eval each arg marked with parse_nodes.evals_into()"""
    if isinstance(step, Subscript):
        return eval_args_subscript(step, user_globals)
    return eval_dataclass(step, user_globals)


def eval_args_subscript(step: Subscript, user_globals: dict) -> Args:
    """subscripts have nested eval exprs so we have a special case"""
    slice1_args = eval_dataclass(step.slice1, user_globals, attr="slice1")
    slice2_args = eval_dataclass(step.slice2, user_globals, attr="slice2")
    return {**slice1_args, **slice2_args}


def eval_dataclass(obj: t.Any, user_globals: dict, attr="") -> Args:
    """
    takes a dataclasss with fields marked by evals_into(), outputs
    dict of evaluated values
    """
    args: Args = {}
    if obj is None:
        return args

    fields = [
        field
        for field in dataclasses.fields(obj)
        if field.metadata.get("evals_into", False)
    ]

    for field in fields:
        evals_into = field.metadata["evals_into"].format(attr=attr)
        to_eval: t.Union[None, RawCode, t.List[RawCode]] = getattr(
            obj, field.name
        )
        if to_eval is None:
            continue
        elif isinstance(to_eval, list):
            result = [eval(f"({code})", user_globals) for code in to_eval]
        else:
            result = eval(f"({to_eval})", user_globals)
        args[evals_into] = result
    return args
