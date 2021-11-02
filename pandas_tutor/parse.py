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

import json
import typing as t
import dataclasses

import libcst as cst
import libcst.matchers as m
import libcst.metadata as cstm


@dataclasses.dataclass
class Position:
    line: int
    ch: int


@dataclasses.dataclass
class Node:
    type: str
    name: t.Optional[str]
    code: str
    start: Position
    end: Position
    children: t.List[Node]  # type: ignore


def parse(code: str) -> Node:
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    sam = NodePositions()
    _ = with_meta.visit(sam)
    return sam.root


def parse_as_json(code: str) -> str:
    node = parse(code)
    return json.dumps(dataclasses.asdict(node), indent=2)


# Assignments also attach the assign target so we know what to display when
# we preview the statement
# def add_target(node, target):
#     node['target'] = target
#     return node


class NodePositions(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

    # Store cst_root because we need its code_for_node method
    cst_root: cst.CSTNode
    root: Node
    stack: t.List[Node]

    def __init__(self):
        self.stack = []
        super().__init__()

    def visit_Module(self, node):
        self.cst_root = node
        self.root = self.make_node(type='Module', node=node)
        self.stack.append(self.root)

    # expressions contain one or more calls / subscripts
    # the tricky part is that the calls are nested in reverse order of what we
    # want to run. so the first call in df.f().g() is the function g() called
    # on df.f() . i'll flatten and reverse the chain so that the child of each
    # expr will be something like [df.f(), df.f().g()].
    def visit_Expr(self, node):
        current = self.stack[-1]
        child = self.make_node(type='Expr', node=node)
        current.children.append(child)
        self.stack.append(child)

    def leave_Expr(self, node):
        current = self.stack[-1]
        current.children = list(reversed(current.children))
        self.stack.pop()

    # Assign appears instead of Expr when the code looks like df = ...
    def visit_Assign(self, node):
        current = self.stack[-1]
        child = self.make_node(type='Assign', node=node)
        current.children.append(child)
        self.stack.append(child)

    def leave_Assign(self, node):
        current = self.stack[-1]
        current.children = list(reversed(current.children))
        self.stack.pop()

    # matches df.f() to get df but not df.f().g()
    @m.call_if_inside(m.Attribute(value=m.Name()))
    @m.visit(m.Attribute())
    def visit_first_attribute_of_chain(self, node):
        current = self.stack[-1]
        name = node.value.value
        child = self.make_node(type='Name', name=name, node=node.value)
        current.children.append(child)

    # Attribute function calls, like pd.melt(df)
    # won't match square(2)
    def visit_Call(self, node):
        current = self.stack[-1]
        name = node.func.attr.value if m.matches(
            node.func, m.Attribute(attr=m.Name())) else None
        child = self.make_node(type='Call', name=name, node=node)

        # HACK: just saves the args as strings. later, we'll essentially use
        # regexes to figure out what the args are. in the longer term, we
        # should actually parse the args properly.
        #
        # it's a bit tricky to implement at the moment since we're flattening
        # the Call structure as we parse. to implement this, we should keep the
        # calls nested, add calls to the stack, and only flatten everything at
        # the very end.
        child.children = [
            self.cst_root.code_for_node(arg) for arg in node.args
        ]

        current.children.append(child)

    # df.iloc[:, 1] or df.loc['hello'] or df['Name']
    def visit_Subscript(self, node):
        name = (node.value.attr.value if m.matches(
            node,
            m.Subscript(value=m.Attribute(attr=m.Name('loc')
                                          | m.Name('iloc')))) else None)
        current = self.stack[-1]
        child = self.make_node(type='Subscript', name=name, node=node)
        current.children.append(child)

    def make_positions(self, node) -> t.Tuple[Position, Position]:
        meta: cstm.CodeRange = self.get_metadata(cstm.PositionProvider, node)

        # subtract 1 from line to make everything 0-indexed
        return (
            Position(line=meta.start.line - 1, ch=meta.start.column),
            Position(line=meta.end.line - 1, ch=meta.end.column),
        )

    def make_node(self, type=None, name=None, node=None):
        assert type is not None
        assert node is not None
        code = self.cst_root.code_for_node(node)
        start, end = self.make_positions(node)
        return Node(type=type,
                    name=name,
                    code=code,
                    start=start,
                    end=end,
                    children=[])


# For debugging; it just logs the nodes it visits
class LoggingVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

    def __init__(self):
        self.depth = 0

    def visit_Expr(self, node):
        self.log(node, 'Expr')
        self.depth += 1

    def leave_Expr(self, node):
        self.depth -= 1

    def visit_Assign(self, node):
        self.log(node, 'Assign')
        self.depth += 1

    def leave_Assign(self, node):
        self.depth -= 1

    def visit_Call(self, node):
        self.log(node, f'Call({len(node.args)} args)')
        self.depth += 1

    def leave_Call(self, node):
        self.depth -= 1

    def visit_Subscript(self, node):
        self.log(node, 'Subscript')
        self.depth += 1

    def leave_Subscript(self, node):
        self.depth -= 1

    def visit_Attribute(self, node):
        self.log(node, node.attr.value)

    def log(self, node, name):
        meta = self.get_metadata(cstm.PositionProvider, node)
        start = meta.start
        end = meta.end

        spaces = '  ' * self.depth
        print(f'{spaces + name + ":": <20} ({start.line}, {start.column}) '
              f'-> ({end.line}, {end.column})')


test = '''
df.loc[1, 'Name']
'''.strip()


def log_test():
    print(test)
    print('\n-----\n')
    tree = cst.parse_module(test)
    with_meta = cstm.MetadataWrapper(tree)
    sam = LoggingVisitor()
    _ = with_meta.visit(sam)
    return


if __name__ == "__main__":
    from pathlib import Path
    test = (Path(__file__).parent /
            'tests/e2e_golden/sort_values_01.py').read_text()
    print(parse_as_json(test))
    # log_test()
