"""
node objects that parse.py creates
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import field
from typing import ClassVar, List, NewType, Optional, TypeVar, Union

from pandas_tutor.util import Axis, CodeRange, Slicer, pd_agg_funcs

T = TypeVar("T")

# Use a distinct type to distinguish between strings that can be eval'd
RawCode = NewType("RawCode", str)


class _ParseTreeEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


@dataclasses.dataclass
class Base:
    type_: str = field(init=False, repr=False)
    code: RawCode
    location: CodeRange

    def __post_init__(self):
        self.type_ = self.__class__.__name__

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def to_json(cls, items: Union[List[Base], Base]):
        return json.dumps(items, indent=2, cls=_ParseTreeEncoder)


@dataclasses.dataclass
class ParsedModule(Base):
    """root of parse tree"""

    statements: List[Statement]


@dataclasses.dataclass
class VerbatimStatement(Base):
    """node that we should just run, like imports"""

    pass


@dataclasses.dataclass
class ChainStatement(Base):
    """node that we have special parse rules for, like function chains"""

    # TODO: should we distinguish between Assign and Exprs?
    chain: List[ChainStep]


Statement = Union[VerbatimStatement, ChainStatement]


@dataclasses.dataclass
class ChainStep(Base):
    """represents a step that we can visualize, or an error"""

    pass


@dataclasses.dataclass
class StartOfChain(ChainStep):
    """the pd in pd.pivot_table, or df in df['Name']"""

    pass


##############################################################################
# Calls
#
# calls and subscripts have arguments that we need to eval. to handle this,
# we'll do the following:
#
# 1. when parsing, we save the raw code for arguments we'll eval later, and
#    mark those fields using the `evals_into` function (see
#    SortValuesCall.label_expr).
# 2. when executing, we eval each field and save the results into
#    run.EvalResult.args. so, we'll take evals_into('labels') and put it into
#    EvalResult.args['labels']
##############################################################################


@dataclasses.dataclass
class Call(ChainStep):
    """base class used for typing"""

    # used when parsing to match functions to Call subclasses
    fn_name: ClassVar


def evals_into(attr: str):
    """marks a field in a dataclass as one that should be eval'd"""
    return field(metadata=dict(evals_into=attr))


@dataclasses.dataclass
class SortValuesCall(Call):
    """
    cols = ['size', 'breed']
    df.sort_values(cols)
    """

    fn_name = "sort_values"

    # Expression that evaluates to labels
    label_expr: RawCode = evals_into("labels")

    # technically the axis can be an expression too...but who does that??
    axis: Axis = "index"


@dataclasses.dataclass
class RenameCall(Call):
    """
    names = {'size': 'SIZE', 'food_cost': 'cost'}
    df.rename(names, axis=1)
    df.rename(axis=1, mapper=names)
    df.rename(columns=names)
    df.rename(index={'sam': 'smae'})
    """

    fn_name = "rename"

    # expression that results in a dict. can sometimes be a function, in which
    # case we need to just pass it through
    mapping_expr: RawCode = evals_into("mapping")

    axis: Axis = "index"


@dataclasses.dataclass
class HeadCall(Call):
    """
    df.head(5)
    df.head()
    df.head(-2)
    """

    fn_name = "head"


@dataclasses.dataclass
class TailCall(Call):
    """
    df.tail(5)
    df.tail()
    df.tail(-2)
    """

    fn_name = "tail"


@dataclasses.dataclass
class PassThroughCall(Call):
    """
    call that we don't know how to draw diagram for, so we should just run it
    and keep going
    """

    fn_name = "PASS_THROUGH"
    func: str


@dataclasses.dataclass
class GroupByCall(Call):
    """
    the labels for grouping are automatically saved into the groupby object,
    so we don't need to get them during parsing

    df.groupby('region')
    df.groupby(['region', 'id'])
    df.groupby(df['region'])
    df.groupby(lambda val: val // 10)
    """

    fn_name = "groupby"

    axis: Axis = "index"


@dataclasses.dataclass
class AggCall(Call):
    """
    catch-all for any function that happens after a groupby. note: some
    functions on groupby objects are transforms, not aggregations, e.g.
    .transform(), .apply(), .cumcount(), etc. and shouldn't be parsed into an
    AggCall

    g = df.groupby('region')
    g.agg('mean')
    g.mean()
    g.std()
    """

    # don't match the actual "agg()" call since we have a special case in the
    # parser for aggregations
    fn_name = "AGG"

    # exhaustive list of aggregation functions from GroupBy objects
    agg_funcs = ["agg", "aggregate", *pd_agg_funcs]

    @classmethod
    def from_passthrough_call(cls, call: PassThroughCall):
        return cls(code=call.code, location=call.location)


@dataclasses.dataclass
class ApplyCall(Call):
    """
    df['region'].apply(len)
    """

    fn_name = "apply"

    axis: Axis = "index"


@dataclasses.dataclass
class AssignCall(Call):
    """
    df.assign(test=2)
    df.assign(temp_f=df['temp_c'] * 9 / 5 + 32)
    """

    fn_name = "assign"

    new_col_labels: List[str]


@dataclasses.dataclass
class DropCall(Call):
    """
    dogs.drop(columns=['type', 'price'])
    dogs.drop(['Labrador Retriever', 'Beagle'])
    """

    fn_name = "drop"

    col_expr: Optional[RawCode] = evals_into("col_labels")
    row_expr: Optional[RawCode] = evals_into("row_labels")


@dataclasses.dataclass
class ResetIndexCall(Call):
    """
    dogs.reset_index(level=1)
    dogs.reset_index(level=[1, 2])
    dogs.reset_index(level=1, drop=True)
    """

    fn_name = "reset_index"

    level_expr: Optional[RawCode] = evals_into("level")
    drop_expr: Optional[RawCode] = evals_into("drop")


@dataclasses.dataclass
class SetIndexCall(Call):
    """
    dogs.set_index('breed', drop=False)
    dogs.set_index('breed', append=True)
    """

    fn_name = "set_index"

    keys_expr: Optional[RawCode] = evals_into("keys")
    # we don't need to track the drop arg
    append_expr: Optional[RawCode] = evals_into("append")


@dataclasses.dataclass
class UnstackCall(Call):
    """
    counts.unstack()
    counts.unstack(level=1)
    counts.unstack(level=[1, 2])
    counts.unstack(level=-1, fill_value=0)
    """

    fn_name = "unstack"

    level_expr: Optional[RawCode] = evals_into("level")


@dataclasses.dataclass
class StackCall(Call):
    """
    counts.stack()
    counts.stack(level=1)
    counts.stack(level=[1, 2])
    counts.stack(level=-1, dropna=True)
    """

    fn_name = "stack"

    level_expr: Optional[RawCode] = evals_into("level")


@dataclasses.dataclass
class PivotCall(Call):
    """
    df.pivot(index='foo', columns='bar', values='baz')
    """

    fn_name = "pivot"

    index_expr: Optional[RawCode] = evals_into("index")
    columns_expr: Optional[RawCode] = evals_into("columns")
    values_expr: Optional[RawCode] = evals_into("values")


@dataclasses.dataclass
class PivotTableCall(Call):
    """
    df.pivot_table(values='D', index=['A', 'B'],
                   columns=['C'], aggfunc=np.sum)
    df.pivot_table(values=['D', 'E'], index=['A', 'C'],
                   aggfunc={'D': np.mean,
                            'E': np.mean})
    """

    fn_name = "pivot_table"

    index_expr: Optional[RawCode] = evals_into("index")
    columns_expr: Optional[RawCode] = evals_into("columns")
    values_expr: Optional[RawCode] = evals_into("values")
    aggfunc_expr: Optional[RawCode] = evals_into("aggfunc")


@dataclasses.dataclass
class MeltCall(Call):
    """
    df.melt(id_vars=['A'], value_vars=['B'])
    df.melt(id_vars=['A'], value_vars=['B'],
            var_name='myVarname', value_name='myValname')
    """

    fn_name = "melt"

    id_vars_expr: Optional[RawCode] = evals_into("id_vars")
    value_vars_expr: Optional[RawCode] = evals_into("value_vars")
    var_name_expr: Optional[RawCode] = evals_into("var_name")
    value_name_expr: Optional[RawCode] = evals_into("value_name")
    col_level_expr: Optional[RawCode] = evals_into("col_level")
    ignore_index_expr: Optional[RawCode] = evals_into("ignore_index")


@dataclasses.dataclass
class MergeCall(Call):
    """
    baby.merge(nyt, left_on='Name', right_on='nyt_name', how='left')
    """

    fn_name = "merge"

    right_expr: Optional[RawCode] = evals_into("right")
    how_expr: Optional[RawCode] = evals_into("how")
    on_expr: Optional[RawCode] = evals_into("on")
    left_on_expr: Optional[RawCode] = evals_into("left_on")
    right_on_expr: Optional[RawCode] = evals_into("right_on")
    left_index_expr: Optional[RawCode] = evals_into("left_index")
    right_index_expr: Optional[RawCode] = evals_into("right_index")
    sort_expr: Optional[RawCode] = evals_into("sort")
    suffixes_expr: Optional[RawCode] = evals_into("suffixes")


@dataclasses.dataclass
class JoinCall(Call):
    """
    baby.join(nyt, on='Name', how='inner', sort=True)
    """

    fn_name = "join"

    other_expr: Optional[RawCode] = evals_into("other")
    on_expr: Optional[RawCode] = evals_into("on")
    how_expr: Optional[RawCode] = evals_into("how")
    sort_expr: Optional[RawCode] = evals_into("sort")


##############################################################################
# Subscripts
##############################################################################


@dataclasses.dataclass
class Subscript(ChainStep):
    """
    hard-codes two slice elements (i've never seen a third slice in pandas
    code, but i could be wrong)
    """

    slicer: Slicer

    slice1: SubscriptEl
    slice2: Optional[SubscriptEl]


@dataclasses.dataclass
class SubsSlice(Base):
    """df.iloc[:3]"""

    pass


@dataclasses.dataclass
class SubsComparison(Base):
    """
    special case for boolean expressions:

        df[df['Count'] > 10]

        col = 'Name'
        df[(df[col] > 10) | (df['Year'] >= 2020)]

    but won't handle cases where the expression runs outside the slide, like:

        mask = df['Count'] > 10
        df[mask]

    (those will go into EvalSlice)
    """

    # this is a list of code expressions that will each eval to one-or-more
    # labels. when parsing, we need to pull these out of each boolean mask
    label_exprs: List[RawCode] = field(
        metadata=dict(evals_into="{attr}_filter_labels")
    )


@dataclasses.dataclass
class SubsEval(Base):
    """
    anything that evals into row/column label(s), like:

        df['Name']
        df[['Name', 'Count']]
        df[df.columns[:4]]

    the evaluated expression can technically be any valid pandas slice,
    like boolean masks that aren't caught by ComparisonSlice.
    if the result isn't a list of labels, then we should just pass it through
    and not try to visualize it
    """

    expr: RawCode = field(metadata=dict(evals_into="{attr}_values"))


SubscriptEl = Union[SubsSlice, SubsComparison, SubsEval]

##############################################################################
# Errors
##############################################################################


@dataclasses.dataclass
class ParseSyntaxError(ChainStep):
    """
    represents an error in parsing. when this happens, we should pass along the
    error for serializing. we don't run the code since libcst produces nicer
    error messages compared to Python
    """

    error_msg: str


@dataclasses.dataclass
class EvalError(ChainStep):
    """represents a step in the chain that caused a runtime error"""

    # TODO: compute code positions for errors
    @classmethod
    def from_node(cls, node: Base):
        return cls(code=node.code, location=node.location)


ParseResult = Union[ParsedModule, ParseSyntaxError]
