'''
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
'''

# For forward type references: https://stackoverflow.com/a/33533514
from __future__ import annotations

import typing as t
from warnings import warn

import libcst as cst
import libcst.matchers as m
import libcst.metadata as cstm

from .parse_nodes import (AggCall, ApplyCall, AssignCall, Axis, ChainStatement,
                          GroupByCall, HeadCall, ParseResult, ParsedModule,
                          ParseSyntaxError, PassThroughCall, RawCode,
                          RenameCall, SortValuesCall, StartOfChain,
                          SubsComparison, Subscript, SubscriptEl, SubsEval,
                          SubsSlice, TailCall, VerbatimStatement)
from .util import CodePosition, CodeRange

T = t.TypeVar('T')


def parse(code: str) -> ParseResult:
    try:
        tree = cst.parse_module(code)
    except cst.ParserSyntaxError as e:
        pos = CodePosition(e.editor_line - 1, e.editor_column)
        return ParseSyntaxError(code=RawCode(code),
                                error_msg=str(e),
                                location=CodeRange(pos, pos))

    with_meta = cstm.MetadataWrapper(tree)
    sam = PandasParser()
    _ = with_meta.visit(sam)
    return sam.root


def parse_as_json(code: str) -> str:
    node = parse(code)
    return ParsedModule.to_json(node)


# Any statement from:
# https://libcst.readthedocs.io/en/latest/nodes.html#statements
# that we don't process and should just execute verbatim, like
# import pandas as pd
is_verbatim_stmt = (m.AnnAssign() | m.Assign() | m.Assert() | m.Del()
                    | m.Global() | m.Import() | m.ImportFrom() | m.Nonlocal()
                    | m.Raise() | m.ClassDef() | m.For() | m.FunctionDef()
                    | m.If() | m.Try() | m.While() | m.With())

is_chain_stmt = m.Expr()

is_attribute_call = m.Call(func=m.Attribute())


def fn_matcher(fn_name: str):
    return m.Call(func=m.Attribute(attr=m.Name(fn_name)))


def fn_name(call: cst.Call):
    func = t.cast(cst.Attribute, call.func)
    return func.attr.value


is_sort_values = fn_matcher('sort_values')
is_rename = fn_matcher('rename')
is_head_or_tail = fn_matcher('head') | fn_matcher('tail')
is_groupby = fn_matcher('groupby')
is_apply = fn_matcher('apply')
is_assign = fn_matcher('assign')

# make sure to update this whenever we add a new call to the section above
is_parsed_call = (is_sort_values | is_rename | is_head_or_tail | is_groupby
                  | is_apply | is_assign)

is_loc_iloc = m.Subscript(value=m.Attribute(attr=m.Name('loc')
                                            | m.Name('iloc')))

is_boolean_slice = (m.Comparison()
                    | m.BinaryOperation(operator=(m.BitOr() | m.BitAnd())))


def get_arg_by_position_or_keyword(
        args: t.Sequence[cst.Arg],
        position: int,
        keyword: t.Optional[str] = None) -> t.Optional[cst.Arg]:
    '''
    some function args can be passed by both position and keyword. if the arg
    is passed by keyword, it should have priority over the position, so:

        df.sort_values('Name')
        df.sort_values(ascending=False, by='Name')

    should all get the Arg for 'Name'
    '''
    if keyword is not None:
        for arg in args:
            if arg.keyword is not None and arg.keyword.value == keyword:
                return arg
    if position >= len(args):
        return None
    return args[position]


def make_axis(value: str) -> Axis:
    return (
        'columns' if value == '1' or 'columns' in value else
        'index' if value == '0' or 'index' in value
        # index is the default for most pandas methods so we'll just fall
        # back to that...maybe we should raise an error in this case instead
        else 'index')


class PandasParser(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

    # Store cst_root because we need its code_for_node method
    cst_root: cst.Module
    root: ParsedModule
    current: t.Optional[ChainStatement] = None

    slice_depth: int

    # captures nodes for ":" and 'Name' from df.loc[:, 'Name']
    slices: t.List[SubscriptEl]

    # captures "col" and 'Year' from df[(df[col] > 10) | (df['Year'] >= 2020)]
    comparison_labels: t.List[RawCode]

    def __init__(self):
        self.slice_depth = 0
        self.slices = []
        self.comparison_labels = []
        super().__init__()

    def visit_Module(self, cst_node):
        self.cst_root = cst_node
        self.root = self.make_node(ParsedModule, cst_node, statements=[])

    def visit_IndentedBlock(self, cst_node):
        return False

    @m.visit(is_verbatim_stmt)
    def make_verbatim_stmt(self, cst_node):
        node = self.make_node(VerbatimStatement, cst_node)
        self.root.statements.append(node)

    @m.visit(is_chain_stmt)
    def visit_chain_stmt(self, cst_node):
        node = self.make_node(ChainStatement, cst_node, chain=[])
        self.root.statements.append(node)
        self.current = node

    @m.leave(is_chain_stmt)
    def leave_current_stmt(self, cst_node):
        self.current = None

    # for things in a chain, we append to chain on _leaving_ a node because of
    # the way chains are nested in the CST. for a chain like df.a().b(), the
    # parse order is b(), then a(), then df. if we append on leaving,
    # then we get the right chain order of df, a(), b().

    # we need to get the df out of:
    # df.f()
    # df['hello']
    @m.call_if_inside(is_chain_stmt)
    @m.leave(m.Name())
    def make_first_in_chain(self, cst_node):
        # we should only do this for the first name in an chain
        if self.current is not None and len(self.current.chain) == 0:
            node = self.make_node(StartOfChain, cst_node)
            self.current.chain.append(node)

    ###########################################################################
    # Calls
    ###########################################################################

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_attribute_call)
    def make_pass_through_call(self, cst_node):
        if m.matches(cst_node, is_parsed_call):
            return

        # special case: any function called on a groupby gets parsed into an
        # AggCall.
        # TODO: don't do this for non-aggregating funcs like .transform()
        if self.current is not None and len(self.current.chain) > 1:
            last = self.current.chain[-1]
            if isinstance(last, GroupByCall):
                node = self.make_call_node(AggCall, cst_node)
                self.current.chain.append(node)
                return

        self.fallback_call(cst_node)

    def fallback_call(self, cst_node):
        '''
        called whenever we don't know how to parse a call. that could be
        when we don't handle the function, or if the function has weird
        arguments that we can't parse.
        '''
        assert self.current is not None, (
            'tried to call fallback when not in a chain!')
        fn_name = cst_node.func.attr.value
        node = self.make_call_node(PassThroughCall, cst_node, fn_name=fn_name)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_sort_values)
    def make_sort_values_call(self, cst_node):
        assert self.current is not None, (
            'tried to call make_sort_values_call when not in a chain!')
        by = get_arg_by_position_or_keyword(cst_node.args, 0, 'by')
        axis_arg = get_arg_by_position_or_keyword(cst_node.args, 1, 'axis')

        label_expr = self.code_for(by.value) if by is not None else ''

        # default sort_values uses rows
        axis = (make_axis(self.code_for(axis_arg.value))
                if axis_arg is not None else 'index')

        node = self.make_call_node(SortValuesCall,
                                   cst_node,
                                   label_expr=label_expr,
                                   axis=axis)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_rename)
    def make_rename_call(self, cst_node):
        assert self.current is not None, (
            'tried to call make_sort_values_call when not in a chain!')
        mapper = get_arg_by_position_or_keyword(cst_node.args, 0, 'mapper')
        index = get_arg_by_position_or_keyword(cst_node.args, 1, 'index')
        columns = get_arg_by_position_or_keyword(cst_node.args, 2, 'columns')
        axis_arg = get_arg_by_position_or_keyword(cst_node.args, 3, 'axis')
        axis = 'index'  # default

        if index is not None:
            mapper = index
            axis = 'index'
        elif columns is not None:
            mapper = columns
            axis = 'columns'
        elif axis_arg is not None:
            axis = make_axis(self.code_for(axis_arg.value))

        if mapper is None:
            self.fallback_call(cst_node)
            return

        node = self.make_call_node(RenameCall,
                                   cst_node,
                                   mapping_expr=self.code_for(mapper.value),
                                   axis=axis)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_head_or_tail)
    def make_head_or_tail(self, cst_node):
        assert self.current is not None, (
            'tried to call make_head_or_tail when not in a chain!')
        name = fn_name(cst_node)
        node = self.make_call_node(HeadCall if name == 'head' else TailCall,
                                   cst_node)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_apply)
    def make_apply(self, cst_node):
        assert self.current is not None, (
            'tried to call make_apply when not in a chain!')
        # axis only available for dataframes...for series, arg 1 is some other
        # arg that we don't care about so we should be careful here
        axis_arg = get_arg_by_position_or_keyword(cst_node.args, 1, 'axis')
        axis = 'index'  # default
        if axis_arg is not None:
            axis = make_axis(self.code_for(axis_arg.value))
        node = self.make_call_node(ApplyCall, cst_node, axis=axis)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_assign)
    def make_assign(self, cst_node: cst.Call):
        assert self.current is not None, (
            'tried to call make_assign when not in a chain!')
        # each kwarg is a new column
        new_col_labels = [
            arg.keyword.value for arg in cst_node.args
            if arg.keyword is not None
        ]

        node = self.make_call_node(AssignCall,
                                   cst_node,
                                   new_col_labels=new_col_labels)
        self.current.chain.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_groupby)
    def make_groupby(self, cst_node):
        assert self.current is not None, (
            'tried to call make_head_or_tail when not in a chain!')
        by = get_arg_by_position_or_keyword(cst_node.args, 0, 'by')
        axis_arg = get_arg_by_position_or_keyword(cst_node.args, 1, 'axis')

        if by is None:
            self.fallback_call(cst_node)
            return

        # default groupby uses rows
        axis = (make_axis(self.code_for(axis_arg.value))
                if axis_arg is not None else 'index')

        node = self.make_call_node(GroupByCall, cst_node, axis=axis)
        self.current.chain.append(node)

    ###########################################################################
    # Subscripts
    ###########################################################################

    # this is tricky!
    # we don't want to treat inner subscripts as a chain e.g. df[df['keep']]
    # so we call this when we recurse into df[df[...]]
    # take care only to call this when we're in a nested slice
    @m.call_if_inside(m.SubscriptElement())
    @m.visit(m.Subscript())
    def enter_inner_subscript(self, cst_node):
        self.slice_depth += 1
        # print(f'{self.code_for(cst_node): <40} ({self.slice_depth})')

    @m.call_if_inside(m.SubscriptElement())
    @m.leave(m.Subscript())
    def leave_inner_subscript(self, cst_node):
        self.slice_depth -= 1

    @m.call_if_inside(is_chain_stmt)
    @m.call_if_not_inside(m.SubscriptElement())
    @m.visit(m.Subscript())
    def enter_top_subscript(self, cst_node):
        pass
        # assert self.slices is None, (
        #     f'tried to enter_top_subscript with leftover slices: '
        #     f'{self.code_for(cst_node)}')
        # self.slices = []

    @m.call_if_inside(is_chain_stmt)
    @m.call_if_not_inside(m.SubscriptElement() | m.Arg())
    @m.leave(m.Subscript())
    def make_subscript(self, cst_node: cst.Subscript):
        assert self.current is not None, (
            'called make_subscript when not in a chain!')
        # HACK: limit subscript parsing depth to 1
        assert self.slice_depth == 0, (
            'called make_subscript in a nested subscript')

        slicer: t.Optional[str] = None
        if m.matches(cst_node, is_loc_iloc):
            slicer = t.cast(cst.Attribute, cst_node.value).attr.value

        n_slices = len(self.slices)
        slice1 = None
        slice2 = None

        if n_slices == 1:
            slice1 = self.slices[0]
        elif n_slices == 2:
            [slice1, slice2, *_] = self.slices
        else:
            warn(f'weird: parsed subscript with {n_slices} slices @\n'
                 f'{self.code_for(cst_node)}\n\n'
                 f'self.slices:\n'
                 f'{self.slices}\n')
            # TODO: have a 'passthrough slice'

        # from dogs["breed"], get location of ["breed"]
        location = (self.location(cst_node.lbracket)
                    | self.location(cst_node.rbracket))
        # if we have a slicer, then we want the '.loc' too
        if slicer is not None:
            location = location | self.location(
                t.cast(cst.Attribute, cst_node.value).dot)

        node = self.make_node(Subscript,
                              cst_node,
                              location=location,
                              slicer=slicer,
                              slice1=slice1,
                              slice2=slice2)
        self.current.chain.append(node)

        self.slices = []

    @m.call_if_inside(is_chain_stmt)
    @m.visit(m.Slice())
    def make_subs_slice(self, cst_node):
        if self.slice_depth > 0:
            # print(f'called make_subs_slice from nested subscript, skipping: '
            #       f'{self.code_for(cst_node)}')
            return
        node = self.make_node(SubsSlice, cst_node)
        self.slices.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.visit(m.Index(value=~is_boolean_slice))
    def make_subs_eval(self, cst_node):
        if self.slice_depth > 0:
            # print(f'called make_subs_eval from nested subscript, skipping: '
            #       f'{self.code_for(cst_node)}')
            return
        node = self.fallback_slice(cst_node)
        self.slices.append(node)

    @m.call_if_inside(is_chain_stmt)
    @m.visit(m.Index(value=is_boolean_slice))
    def enter_subs_comparison(self, cst_node):
        pass

    @m.call_if_inside(is_chain_stmt)
    @m.leave(m.Index(value=is_boolean_slice))
    def make_subs_comparison(self, cst_node):
        assert self.comparison_labels is not None, (
            f'called make_subs_comparison outside a comparison:'
            f'{self.code_for(cst_node)}')
        if len(self.comparison_labels) == 0:
            warn("couldn't parse labels out of comparison, falling back "
                 "to eval slice")
            node = self.fallback_slice(cst_node)
            self.slices.append(node)
            return

        node = self.make_node(SubsComparison,
                              cst_node,
                              label_exprs=self.comparison_labels)
        self.slices.append(node)
        self.comparison_labels = []

    @m.call_if_inside(is_chain_stmt)
    @m.call_if_inside(is_boolean_slice)
    @m.visit(m.Index())
    def record_comparison_label(self, cst_node):
        assert self.comparison_labels is not None, (
            f'called record_comparison_label outside a comparison:'
            f'{self.code_for(cst_node)}')
        # don't look for labels beyond one level of nesting
        if self.slice_depth > 1:
            return
        self.comparison_labels.append(self.code_for(cst_node))

    # fallback to just eval'ing the slice
    def fallback_slice(self, cst_node):
        return self.make_node(SubsEval, cst_node, expr=self.code_for(cst_node))

    ###########################################################################
    # Helpers
    ###########################################################################

    def code_for(self, cst_node):
        return RawCode(self.cst_root.code_for_node(cst_node))

    def location(self, cst_node) -> CodeRange:
        meta = t.cast(cstm.CodeRange,
                      self.get_metadata(cstm.PositionProvider, cst_node))

        # subtract 1 from line to make everything 0-indexed
        start = CodePosition(line=meta.start.line - 1, ch=meta.start.column)
        end = CodePosition(line=meta.end.line - 1, ch=meta.end.column)
        return CodeRange(start, end)

    def make_node(self,
                  cls: t.Type[T],
                  cst_node: cst.CSTNode,
                  location=None,
                  **kwargs) -> T:
        code = self.code_for(cst_node)
        if location is None:
            location = self.location(cst_node)
        return cls(code=code, location=location, **kwargs)  # type: ignore

    def make_call_node(self, cls: t.Type[T], cst_node: cst.Call,
                       **kwargs) -> T:
        '''
        for calls in chain like df.apply(), the location of the call is the
        dot + everything after
        '''
        func = t.cast(cst.Attribute, cst_node.func)
        dot = self.location(func.dot)
        entire_expr = self.location(cst_node)
        location = CodeRange(dot.start, entire_expr.end)

        return self.make_node(cls, cst_node, location=location, **kwargs)


whitespace = (m.Comment() | m.EmptyLine() | m.Newline()
              | m.ParenthesizedWhitespace() | m.SimpleWhitespace()
              | m.TrailingWhitespace() | m.BaseParenthesizableWhitespace())


# For debugging; it just logs the nodes it visits
class LoggingVisitor(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

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
            self.cst_root = node
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

        spaces = '  ' * self.depth
        print(f'{spaces + name + ":": <40} ({code})')
        # print(f'{spaces + name + ":": <20} ({start.line}, {start.column}) '
        #       f'-> ({end.line}, {end.column})')


test = '''
df.loc[1, 'Name']
'''.strip()


def test_logger(code):
    print(code)
    print('\n-----\n')
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    sam = LoggingVisitor()
    _ = with_meta.visit(sam)
    return


def test_parser(code):
    print(code)
    print('\n-----\n')
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    sam = PandasParser()
    _ = with_meta.visit(sam)
    return sam.root


if __name__ == "__main__":
    from pathlib import Path
    test = (Path(__file__).parent /
            'tests/e2e_golden/sort_values_01.py').read_text()
    print(parse_as_json(test))
    # log_test()
