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

import libcst as cst
import libcst.matchers as m
import libcst.metadata as cstm

from .parse_nodes import (Axis, CodePosition, ParsedModule, ChainStatement,
                          PassThroughCall, RawCode, RenameCall, SortValuesCall,
                          StartOfChain, Subscript, VerbatimStatement)

T = t.TypeVar('T')


def parse(code: str) -> ParsedModule:
    tree = cst.parse_module(code)
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


is_sort_values = fn_matcher('sort_values')
is_rename = fn_matcher('rename')

is_parsed_call = is_sort_values | is_rename

is_loc_iloc = m.Subscript(value=m.Attribute(attr=m.Name('loc')
                                            | m.Name('iloc')))


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
    subscript_depth: int = 0

    def visit_Module(self, cst_node):
        self.cst_root = cst_node
        self.root = self.make_node(ParsedModule, cst_node, statements=[])

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

    @m.call_if_inside(is_chain_stmt)
    @m.leave(is_attribute_call)
    def make_pass_through_call(self, cst_node):
        if m.matches(cst_node, is_parsed_call):
            return
        self.fallback_call(cst_node)

    def fallback_call(self, cst_node):
        '''
        called whenever we don't know how to parse a call. that could be
        when we don't handle the function, or if the function has weird
        arguments that we can't parse.
        '''
        assert self.current.chain is not None, (
            'tried to call fallback when not in a chain!')
        fn_name = cst_node.func.attr.value
        node = self.make_node(PassThroughCall, cst_node, fn_name=fn_name)
        self.current.chain.append(node)

    @m.leave(is_sort_values)
    def make_sort_values_call(self, cst_node):
        by = get_arg_by_position_or_keyword(cst_node.args, 0, 'by')
        axis_arg = get_arg_by_position_or_keyword(cst_node.args, 1, 'axis')

        if by is None:
            self.fallback_call(cst_node)
            return

        label_expr = self.code_for(by.value)

        # default sort_values uses rows
        axis = (make_axis(self.code_for(axis_arg.value))
                if axis_arg is not None else 'index')

        node = self.make_node(SortValuesCall,
                              cst_node,
                              label_expr=label_expr,
                              axis=axis)
        self.current.chain.append(node)

    @m.leave(is_rename)
    def make_rename_call(self, cst_node):
        # TODO
        self.fallback_call(cst_node)
        # node = self.make_node(RenameCall, cst_node, mapping_expr='<wip>')
        # self.current.chain.append(node)

    # HACK: don't visit nested subscripts so we won't make a node for the
    # df['Name'] in df[df['Name'] == 'Liam']
    @m.call_if_inside(is_chain_stmt)
    @m.visit(m.Subscript())
    def entering_subscript(self, node):
        self.subscript_depth += 1

    @m.call_if_inside(is_chain_stmt)
    @m.leave(m.Subscript())
    def make_subscript(self, cst_node):
        self.subscript_depth -= 1
        if self.subscript_depth > 0:
            return
        # TODO

        attr = (cst_node.value.attr.value
                if m.matches(cst_node, is_loc_iloc) else None)
        node = self.make_node(Subscript, cst_node, attr=attr, elements=[])
        self.current.chain.append(node)

    def code_for(self, cst_node):
        return RawCode(self.cst_root.code_for_node(cst_node))

    def make_positions(self, cst_node) -> t.Tuple[CodePosition, CodePosition]:
        meta: cstm.CodeRange = self.get_metadata(cstm.PositionProvider,
                                                 cst_node)

        # subtract 1 from line to make everything 0-indexed
        return (
            CodePosition(line=meta.start.line - 1, ch=meta.start.column),
            CodePosition(line=meta.end.line - 1, ch=meta.end.column),
        )

    def make_node(self, cls: t.Type[T], cst_node: cst.CSTNode, **kwargs) -> T:
        code = self.code_for(cst_node)
        start, end = self.make_positions(cst_node)
        return cls(code=code, start=start, end=end, **kwargs)  # type: ignore


whitespace = (m.Comment() | m.EmptyLine() | m.Newline()
              | m.ParenthesizedWhitespace() | m.SimpleWhitespace()
              | m.TrailingWhitespace() | m.BaseParenthesizableWhitespace())


# For debugging; it just logs the nodes it visits
class LoggingVisitor(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

    cst_root: cst.CSTNode
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
