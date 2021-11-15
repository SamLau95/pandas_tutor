'''
node objects that parse.py creates
'''
from __future__ import annotations

import dataclasses
import json
import typing as t
from dataclasses import field

# Use a distinct type to distinguish between strings that can be eval'd
RawCode = t.NewType('RawCode', str)


class _ParseTreeEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


@dataclasses.dataclass
class CodePosition:
    '''points to a location within the original code string'''
    line: int
    ch: int


@dataclasses.dataclass
class Base:
    type_: str = field(init=False)
    code: RawCode
    start: CodePosition
    end: CodePosition

    def __post_init__(self):
        self.type_ = self.__class__.__name__

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def to_json(cls, items: t.Union[t.List[Base], Base]):
        return json.dumps(items, indent=2, cls=_ParseTreeEncoder)


@dataclasses.dataclass
class ParsedModule(Base):
    '''root of parse tree'''
    statements: t.List[Statement]


@dataclasses.dataclass
class VerbatimStatement(Base):
    '''node that we should just run, like imports'''
    pass


@dataclasses.dataclass
class ChainStatement(Base):
    '''node that we have special parse rules for, like function chains'''
    # TODO: should we distinguish between Assign and Exprs?
    chain: t.List[ChainStep]


Statement = t.Union[VerbatimStatement, ChainStatement]


@dataclasses.dataclass
class StartOfChain(Base):
    '''the pd in pd.pivot_table, or df in df['Name']'''
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


def evals_into(attr: str):
    return field(metadata=dict(evals_into=attr))


Axis = t.Literal['index', 'columns']


@dataclasses.dataclass
class SortValuesCall(Base):
    '''
    cols = ['size', 'breed']
    df.sort_values(cols)
    '''
    fn_name = 'sort_values'

    # Expression that evaluates to labels
    label_expr: RawCode = evals_into('labels')

    # technically the axis can be an expression too...but who does that??
    axis: Axis = 'index'


@dataclasses.dataclass
class RenameCall(Base):
    '''
    names = {'size': 'SIZE', 'food_cost': 'cost'}
    df.rename(names, axis=1)
    df.rename(axis=1, mapper=names)
    df.rename(columns=names)
    df.rename(index={'sam': 'smae'})
    '''
    fn_name = 'rename'

    # expression that results in a dict. can sometimes be a function, in which
    # case we need to just pass it through
    mapping_expr: RawCode = evals_into('mapping')

    axis: Axis = 'index'


@dataclasses.dataclass
class HeadCall(Base):
    '''
    df.head(5)
    df.head()
    df.head(-2)
    '''
    fn_name = 'head'


@dataclasses.dataclass
class TailCall(Base):
    '''
    df.tail(5)
    df.tail()
    df.tail(-2)
    '''
    fn_name = 'tail'


@dataclasses.dataclass
class PassThroughCall(Base):
    '''
    call that we don't know how to draw diagram for, so we should just run it
    and keep going
    '''
    fn_name: str


# make sure to update this whenever we add new call node
Call = t.Union[SortValuesCall, RenameCall, HeadCall, TailCall, PassThroughCall]

##############################################################################
# Subscripts
##############################################################################

Slicer = t.Literal['loc', 'iloc', None]


@dataclasses.dataclass
class Subscript(Base):
    '''
    hard-codes one or two slice elements (i've never seen a third slice in
    pandas code, but i could be wrong)
    '''
    slicer: Slicer

    slice1: SubscriptEl
    slice2: t.Optional[SubscriptEl]


@dataclasses.dataclass
class SubsSlice(Base):
    '''df.iloc[:3]'''
    pass


@dataclasses.dataclass
class SubsComparison(Base):
    '''
    special case for boolean expressions:

        df[df['Count'] > 10]

        col = 'Name'
        df[(df[col] > 10) | (df['Year'] >= 2020)]

    but won't handle cases where the expression runs outside the slide, like:

        mask = df['Count'] > 10
        df[mask]

    (those will go into EvalSlice)
    '''
    # this is a list of code expressions that will each eval to one-or-more
    # labels. when parsing, we need to pull these out of each boolean mask
    label_exprs: t.List[RawCode] = field(metadata=dict(
        evals_into='{attr}_labels'))


@dataclasses.dataclass
class SubsEval(Base):
    '''
    anything that evals into row/column label(s), like:

        df['Name']
        df[['Name', 'Count']]
        df[df.columns[:4]]

    the evaluated expression can technically be any valid pandas slice,
    like boolean masks that aren't caught by ComparisonSlice.
    if the result isn't a list of labels, then we should just pass it through
    and not try to visualize it
    '''
    expr: RawCode = field(metadata=dict(evals_into='{attr}_values'))


SubscriptEl = t.Union[SubsSlice, SubsComparison, SubsEval]

ChainStep = t.Union[StartOfChain, Call, Subscript]
