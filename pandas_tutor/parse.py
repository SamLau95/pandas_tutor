"""
parses a pandas snippet using libcst. the important thing here is to get the
positions of each expression within the snippet so that we can selectively run
parts of it. there are a bunch of hard-coded heuristics so that each step in
the result hopefully corresponds to one new dataframe.

in the future it would be ideal to hook into bdb directly like python tutor
does. that way we step through the code itself, and it'd be a lot easier to
integrate into python tutor's existing backend.

right now i'm not sure how to make bdb step through individual function calls
in a chain. it doesn't seem to be the default as this pytutor link shows:
https://pythontutor.com/visualize.html#code=s%20%3D%20'hello%20world%20!!%20'%0Atest%20%3D%20s.strip%28%29.replace%28'%20',%20'!'%29.split%28'!'%29%0Aprint%28test%29&cumulative=false&curInstr=2&heapPrimitives=nevernest&mode=display&origin=opt-frontend.js&py=3&rawInputLstJSON=%5B%5D&textReferences=false
"""

# For forward type references: https://stackoverflow.com/a/33533514
from __future__ import annotations

import typing as t
from warnings import warn

import libcst as cst
import libcst.matchers as m
import libcst.metadata as cstm

from pandas_tutor import util
from pandas_tutor.util import CodePosition, CodeRange

from .parse_nodes import (
    AggCall,
    ApplyCall,
    AssignCall,
    Axis,
    Call,
    ChainStatement,
    ChainStep,
    DropCall,
    GroupByCall,
    HeadCall,
    JoinCall,
    MeltCall,
    MergeCall,
    ParsedModule,
    ParseResult,
    ParseSyntaxError,
    PassThroughCall,
    PivotCall,
    PivotTableCall,
    RawCode,
    RenameCall,
    ResetIndexCall,
    SetIndexCall,
    SortValuesCall,
    StackCall,
    StartOfChain,
    SubsComparison,
    Subscript,
    SubscriptEl,
    SubsEval,
    SubsSlice,
    TailCall,
    UnstackCall,
    VerbatimStatement,
)

T = t.TypeVar("T")


def parse(code: str) -> ParseResult:
    try:
        tree = cst.parse_module(code)
    except cst.ParserSyntaxError as e:
        pos = CodePosition(e.editor_line - 1, e.editor_column)
        return ParseSyntaxError(
            code=RawCode(code), error_msg=str(e), location=CodeRange(pos, pos)
        )

    with_meta = cstm.MetadataWrapper(tree)
    positions = with_meta.resolve(cstm.PositionProvider)
    sam = PandasParser(tree, positions)
    _ = with_meta.visit(sam)
    return sam.root


def parse_as_json(code: str) -> str:
    node = parse(code)
    return ParsedModule.to_json(node)


# Any statement from:
# https://libcst.readthedocs.io/en/latest/nodes.html#statements
# that we don't process and should just execute verbatim, like:
#
# >>> import pandas as pd
#
# we actually don't need this variable anymore since we'll just use an else:
# statement in our top-level visitor
#
# is_verbatim_stmt = (
#     m.AnnAssign()
#     | m.AugAssign()
#     | m.Assert()
#     | m.Del()
#     | m.Global()
#     | m.Import()
#     | m.ImportFrom()
#     | m.Nonlocal()
#     | m.Raise()
#     | m.ClassDef()
#     | m.For()
#     | m.FunctionDef()
#     | m.If()
#     | m.Try()
#     | m.While()
#     | m.With()
# )

# parse expressions and assignments into chains
#
# NOTE: need to update this if we want handle annotated assignments
# (x: int = 5) or augmenting assignments (x += 5)
is_chain_stmt = m.Expr() | m.Assign()

# Used to ensure that we don't recurse into nested calls / subscripts
is_argument = m.Arg() | m.SubscriptElement()

is_attribute_call = m.Call(func=m.Attribute())


def matches(call_cls: t.Type[Call]) -> m.Call:
    # returns libcst matcher from a parse_node.Call subclass
    return m.Call(func=m.Attribute(attr=m.Name(call_cls.fn_name)))


# set of all parsed function calls
parsed_calls = {cls.fn_name for cls in Call.__subclasses__()}


def fn_name(call: cst.Call):
    func = t.cast(cst.Attribute, call.func)
    return func.attr.value


def is_parsed_call(call: cst.Call) -> bool:
    return fn_name(call) in parsed_calls


is_loc_iloc = m.Subscript(
    value=m.Attribute(attr=m.Name("loc") | m.Name("iloc"))
)

is_boolean_slice = m.Comparison() | m.BinaryOperation(
    operator=(m.BitOr() | m.BitAnd())
)


def get_arg(
    args: t.Sequence[cst.Arg], position: int, keyword: t.Optional[str] = None
) -> t.Optional[cst.Arg]:
    """
    some function args can be passed by both position and keyword. if the arg
    is passed by keyword, it should have priority over the position, so:

        df.sort_values('Name')
        df.sort_values(ascending=False, by='Name')

    should all get the Arg for 'Name'
    """
    if keyword is not None:
        for arg in args:
            if arg.keyword is not None and arg.keyword.value == keyword:
                return arg
    if position >= len(args):
        return None

    arg = args[position]
    return arg if arg.keyword is None else None


def make_axis(value: str) -> Axis:
    return (
        "columns"
        if value == "1" or "columns" in value
        else "index"
        if value == "0" or "index" in value
        # index is the default for most pandas methods so we'll just fall
        # back to that...maybe we should raise an error in this case instead
        else "index"
    )


class ParserBase(m.MatcherDecoratableVisitor):
    """base class for our libcst node visitors"""

    cst_root: cst.Module

    # We need to initialize with this rather than use metadata since subclasses
    # will visit subtrees of the module and metadata deps only work on
    # module-level visitors.
    positions: t.Mapping[cst.CSTNode, cstm.CodeRange]

    def __init__(
        self,
        cst_root: cst.Module,
        positions: t.Mapping[cst.CSTNode, cstm.CodeRange],
    ):
        super().__init__()
        self.cst_root = cst_root
        self.positions = positions
        self.__post_init__()

    def __post_init__(self):
        """called after __init__() to let subclasses initialize other fields"""
        pass

    @classmethod
    def from_parent(cls, parent: ParserBase):
        return cls(parent.cst_root, parent.positions)

    def code_for(self, cst_node):
        return RawCode(self.cst_root.code_for_node(cst_node))

    def location(self, cst_node) -> CodeRange:
        code_range = self.positions[cst_node]
        # subtract 1 from line to make everything 0-indexed
        start = CodePosition(
            line=code_range.start.line - 1, ch=code_range.start.column
        )
        end = CodePosition(
            line=code_range.end.line - 1, ch=code_range.end.column
        )
        return CodeRange(start, end)

    def make_node(
        self, cls: t.Type[T], cst_node: cst.CSTNode, location=None, **kwargs
    ) -> T:
        code = self.code_for(cst_node)
        if location is None:
            location = self.location(cst_node)
        return cls(code=code, location=location, **kwargs)  # type: ignore


class PandasParser(ParserBase):
    """top level visitor that handles statements"""

    root: ParsedModule

    def visit_Module(self, cst_node: cst.Module):
        statements = util.flatmap(self.parse_statements, cst_node.body)
        self.root = self.make_node(
            ParsedModule, cst_node, statements=list(statements)
        )

    def parse_statements(
        self,
        stmts: t.Union[cst.BaseCompoundStatement, cst.SimpleStatementLine],
    ) -> t.List[t.Union[VerbatimStatement, ChainStatement]]:
        if isinstance(stmts, cst.BaseCompoundStatement):
            return [self.make_verbatim_stmt(stmts)]

        statements = []
        for stmt in stmts.body:
            if m.matches(stmt, is_chain_stmt):
                chain = ChainParser.from_parent(self)
                stmt.visit(chain)
                statements.append(chain.node)
            else:
                statements.append(self.make_verbatim_stmt(stmt))
        return statements

    def make_verbatim_stmt(self, cst_node):
        return self.make_node(VerbatimStatement, cst_node)


class ChainParser(ParserBase):
    """visits a chain statement, stores resulting node in self.node"""

    node: ChainStatement

    @property
    def _chain(self) -> t.List[ChainStep]:
        """convenience to get current chain"""
        return self.node.chain

    def _append(self, step: ChainStep) -> None:
        """convenience to append to chain"""
        self._chain.append(step)

    def on_visit(self, cst_node):
        if not hasattr(self, "node"):
            # we only reach this on the very first visit
            if not isinstance(cst_node, cst.BaseSmallStatement):
                warn(
                    "used ChainParser to visit a non-statement: "
                    f"{self.code_for(cst_node)}"
                )
            self.node = self.make_node(ChainStatement, cst_node, chain=[])

        return not (
            # skip all arguments so we don't recurse into nested function calls
            # and subscripts
            m.matches(cst_node, is_argument)
            # also skip the lhs of the = for assignments
            or isinstance(cst_node, cst.AssignTarget)
        )

    def leave_Subscript(self, cst_node: cst.Subscript):
        # special case: use separate parser for subscripts since they require
        # different logic than function calls
        subs_parser = SubscriptParser.from_parent(self)
        cst_node.visit(subs_parser)
        self._append(subs_parser.step)

    def fallback_call(self, cst_node):
        """
        called whenever we don't know how to parse a call. that could be
        when we don't handle the function, or if the function has weird
        arguments that we can't parse.
        """
        func = cst_node.func.attr.value
        step = self.make_call_node(PassThroughCall, cst_node, func=func)
        self._append(step)

    # for things in a chain, we append to chain on _leaving_ a node because of
    # the way chains are nested in the CST. for a chain like df.a().b(), the
    # parse order is b(), then a(), then df. if we append on leaving,
    # then we get the right chain order of df, a(), b().

    # gets the df out of:
    # df.f()
    # df['hello']
    @m.leave(m.Name())
    def make_chain_start(self, cst_node):
        # we should only do this for the first name in an chain, since for
        # `df.assign` both `df` and `assign` are Names
        if len(self._chain) == 0:
            step = self.make_node(StartOfChain, cst_node)
            self._append(step)

    @m.leave(is_attribute_call)
    def make_pass_through_call(self, cst_node):
        if is_parsed_call(cst_node):
            return

        # special case: make an AggCall if the last call was a GroupBy and
        # we're using an agg function
        if len(self._chain) > 1:
            last = self._chain[-1]
            if isinstance(last, GroupByCall):
                func_name: str = cst_node.func.attr.value
                if func_name in AggCall.agg_funcs:
                    node = self.make_call_node(AggCall, cst_node)
                    self._append(node)
                    return
        # TODO: handle transforming functions like `.transform`

        self.fallback_call(cst_node)

    @m.leave(matches(HeadCall) | matches(TailCall))
    def make_head_or_tail(self, cst_node):
        name = fn_name(cst_node)
        node = self.make_call_node(
            HeadCall if name == "head" else TailCall, cst_node
        )
        self._append(node)

    @m.leave(matches(SortValuesCall))
    def make_sort_values_call(self, cst_node):
        label_expr = self.get_arg_code(cst_node.args, 0, "by")
        axis_arg = self.get_arg_code(cst_node.args, 1, "axis")
        axis = make_axis(axis_arg) if axis_arg is not None else "index"

        node = self.make_call_node(
            SortValuesCall, cst_node, label_expr=label_expr, axis=axis
        )
        self._append(node)

    @m.leave(matches(DropCall))
    def make_drop_call(self, cst_node):
        labels = self.get_arg_code(cst_node.args, 0, "labels")
        axis_arg = self.get_arg_code(cst_node.args, 1, "axis")
        row_expr = self.get_arg_code(cst_node.args, 2, "index")
        col_expr = self.get_arg_code(cst_node.args, 3, "columns")
        axis = make_axis(axis_arg) if axis_arg is not None else "index"

        if labels is not None:
            if axis == "columns":
                col_expr = labels
            else:
                row_expr = labels

        node = self.make_call_node(
            DropCall, cst_node, col_expr=col_expr, row_expr=row_expr
        )
        self._append(node)

    @m.leave(matches(RenameCall))
    def make_rename_call(self, cst_node):
        mapper = get_arg(cst_node.args, 0, "mapper")
        index = get_arg(cst_node.args, 1, "index")
        columns = get_arg(cst_node.args, 2, "columns")
        axis_arg = get_arg(cst_node.args, 3, "axis")
        axis = "index"  # default

        if index is not None:
            mapper = index
            axis = "index"
        elif columns is not None:
            mapper = columns
            axis = "columns"
        elif axis_arg is not None:
            axis = make_axis(self.code_for(axis_arg.value))

        if mapper is None:
            self.fallback_call(cst_node)
            return

        node = self.make_call_node(
            RenameCall,
            cst_node,
            mapping_expr=self.code_for(mapper.value),
            axis=axis,
        )
        self._append(node)

    @m.leave(matches(ApplyCall))
    def make_apply(self, cst_node):
        # axis only available for dataframes...for series, arg 1 is some other
        # arg that we don't care about so we should be careful here
        axis_arg = self.get_arg_code(cst_node.args, 1, "axis")
        axis = make_axis(axis_arg) if axis_arg is not None else "index"

        node = self.make_call_node(ApplyCall, cst_node, axis=axis)
        self._append(node)

    @m.leave(matches(AssignCall))
    def make_assign(self, cst_node: cst.Call):
        # each kwarg is a new column
        new_col_labels = [
            arg.keyword.value
            for arg in cst_node.args
            if arg.keyword is not None
        ]

        node = self.make_call_node(
            AssignCall, cst_node, new_col_labels=new_col_labels
        )
        self._append(node)

    @m.leave(matches(GroupByCall))
    def make_groupby(self, cst_node):
        axis_arg = self.get_arg_code(cst_node.args, 1, "axis")
        axis = make_axis(axis_arg) if axis_arg is not None else "index"

        node = self.make_call_node(GroupByCall, cst_node, axis=axis)
        self._append(node)

    @m.leave(matches(ResetIndexCall))
    def make_reset_index(self, cst_node):
        level_expr = self.get_arg_code(cst_node.args, 0, "level")
        drop_expr = self.get_arg_code(cst_node.args, 1, "drop")

        node = self.make_call_node(
            ResetIndexCall,
            cst_node,
            level_expr=level_expr,
            drop_expr=drop_expr,
        )
        self._append(node)

    @m.leave(matches(SetIndexCall))
    def make_set_index(self, cst_node):
        keys_expr = self.get_arg_code(cst_node.args, 0, "keys")
        append_expr = self.get_arg_code(cst_node.args, 2, "append")

        node = self.make_call_node(
            SetIndexCall,
            cst_node,
            keys_expr=keys_expr,
            append_expr=append_expr,
        )
        self._append(node)

    @m.leave(matches(UnstackCall))
    def make_unstack(self, cst_node):
        level_expr = self.get_arg_code(cst_node.args, 0, "level")

        node = self.make_call_node(
            UnstackCall,
            cst_node,
            level_expr=level_expr,
        )
        self._append(node)

    @m.leave(matches(StackCall))
    def make_stack(self, cst_node):
        level_expr = self.get_arg_code(cst_node.args, 0, "level")

        node = self.make_call_node(
            StackCall,
            cst_node,
            level_expr=level_expr,
        )
        self._append(node)

    @m.leave(matches(PivotCall))
    def make_pivot(self, cst_node: cst.Call):
        index_expr = self.get_arg_code(cst_node.args, 0, "index")
        columns_expr = self.get_arg_code(cst_node.args, 1, "columns")
        values_expr = self.get_arg_code(cst_node.args, 2, "values")

        node = self.make_call_node(
            PivotCall,
            cst_node,
            index_expr=index_expr,
            columns_expr=columns_expr,
            values_expr=values_expr,
        )
        self._append(node)

    @m.leave(matches(PivotTableCall))
    def make_pivot_table(self, cst_node: cst.Call):
        values_expr = self.get_arg_code(cst_node.args, 0, "values")
        index_expr = self.get_arg_code(cst_node.args, 1, "index")
        columns_expr = self.get_arg_code(cst_node.args, 2, "columns")
        aggfunc_expr = self.get_arg_code(cst_node.args, 3, "aggfunc")

        node = self.make_call_node(
            PivotTableCall,
            cst_node,
            index_expr=index_expr,
            columns_expr=columns_expr,
            values_expr=values_expr,
            aggfunc_expr=aggfunc_expr,
        )
        self._append(node)

    @m.leave(matches(MeltCall))
    def make_melt(self, cst_node: cst.Call):
        id_vars_expr = self.get_arg_code(cst_node.args, 0, "id_vars")
        value_vars_expr = self.get_arg_code(cst_node.args, 1, "value_vars")
        var_name_expr = self.get_arg_code(cst_node.args, 2, "var_name")
        value_name_expr = self.get_arg_code(cst_node.args, 3, "value_name")
        col_level_expr = self.get_arg_code(cst_node.args, 4, "col_level")
        ignore_index_expr = self.get_arg_code(cst_node.args, 5, "ignore_index")

        node = self.make_call_node(
            MeltCall,
            cst_node,
            id_vars_expr=id_vars_expr,
            value_vars_expr=value_vars_expr,
            var_name_expr=var_name_expr,
            value_name_expr=value_name_expr,
            col_level_expr=col_level_expr,
            ignore_index_expr=ignore_index_expr,
        )
        self._append(node)

    @m.leave(matches(MergeCall))
    def make_merge(self, cst_node: cst.Call):
        right_expr = self.get_arg_code(cst_node.args, 0, "right")
        how_expr = self.get_arg_code(cst_node.args, 1, "how")
        on_expr = self.get_arg_code(cst_node.args, 2, "on")
        left_on_expr = self.get_arg_code(cst_node.args, 3, "left_on")
        right_on_expr = self.get_arg_code(cst_node.args, 4, "right_on")
        left_index_expr = self.get_arg_code(cst_node.args, 5, "left_index")
        right_index_expr = self.get_arg_code(cst_node.args, 6, "right_index")
        sort_expr = self.get_arg_code(cst_node.args, 7, "sort")
        suffixes_expr = self.get_arg_code(cst_node.args, 8, "suffixes")

        node = self.make_call_node(
            MergeCall,
            cst_node,
            right_expr=right_expr,
            how_expr=how_expr,
            on_expr=on_expr,
            left_on_expr=left_on_expr,
            right_on_expr=right_on_expr,
            left_index_expr=left_index_expr,
            right_index_expr=right_index_expr,
            sort_expr=sort_expr,
            suffixes_expr=suffixes_expr,
        )
        self._append(node)

    @m.leave(matches(JoinCall))
    def make_join(self, cst_node: cst.Call):
        other_expr = self.get_arg_code(cst_node.args, 0, "other")
        on_expr = self.get_arg_code(cst_node.args, 1, "on")
        how_expr = self.get_arg_code(cst_node.args, 2, "how")
        sort_expr = self.get_arg_code(cst_node.args, 5, "sort")

        node = self.make_call_node(
            JoinCall,
            cst_node,
            other_expr=other_expr,
            on_expr=on_expr,
            how_expr=how_expr,
            sort_expr=sort_expr,
        )
        self._append(node)

    def make_call_node(self, cls: t.Type[T], cst_node: cst.Call, **kwargs) -> T:
        """
        for calls in chain like df.apply(), the location of the call is the
        dot + everything after
        """
        func = t.cast(cst.Attribute, cst_node.func)
        dot = self.location(func.dot)
        entire_expr = self.location(cst_node)
        location = CodeRange(dot.start, entire_expr.end)

        return self.make_node(cls, cst_node, location=location, **kwargs)

    def get_arg_code(
        self,
        args: t.Sequence[cst.Arg],
        position: int,
        keyword: t.Optional[str] = None,
    ) -> t.Optional[RawCode]:
        arg = get_arg(args, position, keyword)
        return arg if arg is None else self.code_for(arg.value)


class SubscriptParser(ParserBase):
    """
    special parser for subscript expressions, stores resulting node in
    self.step
    """

    step: Subscript

    def on_visit(self, node):
        if not isinstance(node, cst.Subscript):
            warn(
                "used SubscriptParser to visit a non-subscript: "
                f"{self.code_for(node)}"
            )
            return False

        slicer: t.Optional[str] = None
        if m.matches(node, is_loc_iloc):
            slicer = t.cast(cst.Attribute, node.value).attr.value

        # from dogs["breed"], get location of ["breed"]
        location = self.location(node.lbracket) | self.location(node.rbracket)

        # if we have a slicer, then we want the '.loc' too
        if slicer is not None:
            location = location | self.location(
                t.cast(cst.Attribute, node.value).dot
            )

        n_slices = len(node.slice)
        slice1 = (
            self.parse_slice(node.slice[0].slice) if n_slices >= 1 else None
        )
        slice2 = (
            self.parse_slice(node.slice[1].slice) if n_slices >= 2 else None
        )
        if n_slices > 2:
            warn(
                f"weird: parsed subscript with {n_slices} slices @\n"
                f"{self.code_for(node)}"
            )

        self.step = self.make_node(
            Subscript,
            node,
            location=location,
            slicer=slicer,
            slice1=slice1,
            slice2=slice2,
        )

        # We do everything within on_visit
        return False

    def parse_slice(self, node: cst.BaseSlice) -> t.Optional[SubscriptEl]:
        if m.matches(node, m.Slice()):
            return self.make_node(SubsSlice, node)
        elif m.matches(node, m.Index(value=is_boolean_slice)):
            node = t.cast(cst.Index, node)
            extractor = ExtractLiteralIndexes.from_parent(self)
            node.value.visit(extractor)
            return self.make_node(
                SubsComparison,
                node,
                label_exprs=extractor.labels,
            )
        elif m.matches(node, m.Index(value=~is_boolean_slice)):
            # the fallback case: just eval the slice expression
            return self.make_node(SubsEval, node, expr=self.code_for(node))
        else:
            warn(
                f"weird slice type, defaulting to empty slice:\n"
                f"{self.code_for(node)}"
            )
            return self.make_node(SubsSlice, node)


class ExtractLiteralIndexes(ParserBase):
    """
    special parser to get all simple index values out of a subscript index.
    pandas has expressions that look like this:

        df2[df2["E"].isin(["two", "four"])]

    where we want to get the "E" label out of the inner subscript.

    so we use this parser on Expr nodes to get:

    df[0]                                 -> ["0"]
    df['hello']                           -> ["'hello'"]
    (df[col] > 0) & (df['sam'] == 2)      -> ["col", "'sam'"]
    (df[df['nested']]) & (df['sam'] == 2) -> ["'sam'"]

    but the current implementation doesn't try to distinguish iloc from loc:

    df.iloc[0]                            -> ["0"]
    """

    labels: t.List[RawCode]
    _depth: int

    @property
    def _is_nested(self):
        return self._depth > 1

    def on_visit(self, cst_node):
        if not hasattr(self, "labels"):
            if not isinstance(cst_node, cst.BaseExpression):
                warn(
                    "used ExtractLiteralIndexes to visit a non-expression: "
                    f"{self.code_for(cst_node)}"
                )
            self.labels = []
            self._depth = 0
        return super().on_visit(cst_node)

    def visit_Subscript(self, cst_node):
        self._depth += 1

    def leave_Subscript(self, cst_node):
        self._depth -= 1

    @m.visit(m.Index())
    def record_index(self, cst_node: cst.Index):
        if self._is_nested:
            return

        val = cst_node.value
        if isinstance(val, (cst.BaseString, cst.BaseNumber, cst.Name)):
            self.labels.append(self.code_for(val))


whitespace = (
    m.Comment()
    | m.EmptyLine()
    | m.Newline()
    | m.ParenthesizedWhitespace()
    | m.SimpleWhitespace()
    | m.TrailingWhitespace()
    | m.BaseParenthesizableWhitespace()
)


# For debugging; it just logs the nodes it visits
class LoggingVisitor(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider,)

    cst_root: t.Optional[cst.Module]
    depth: int

    def __init__(self):
        self.depth = 0
        self.cst_root = None
        super().__init__()

    def on_visit(self, node):
        if m.matches(node, whitespace):
            return False
        if self.cst_root is None:
            self.cst_root = t.cast(cst.Module, node)
            return True

        self.log(node)
        self.depth += 1
        return True

    def on_leave(self, node):
        if m.matches(node, whitespace):
            return
        self.depth -= 1

    def log(self, node):
        assert self.cst_root is not None
        name = node.__class__.__name__
        code = self.cst_root.code_for_node(node)
        # meta = self.get_metadata(cstm.PositionProvider, node)
        # start = meta.start
        # end = meta.end

        spaces = "  " * self.depth
        print(f'{spaces + name + ":": <40} ({code})')
        # print(f'{spaces + name + ":": <20} ({start.line}, {start.column}) '
        #       f'-> ({end.line}, {end.column})')


def test_logger(code):
    print(code)
    print("\n-----\n")
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    sam = LoggingVisitor()
    _ = with_meta.visit(sam)
    return


def test_parser(code):
    print(code)
    print("\n-----\n")
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    positions = with_meta.resolve(cstm.PositionProvider)
    sam = PandasParser(tree, positions)
    _ = with_meta.visit(sam)
    return sam.root
