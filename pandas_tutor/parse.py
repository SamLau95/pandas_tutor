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

this code:

    (df
     .sort_values('Name')
     .groupby('Sex')
     ['Count']
     .mean()
    )

produces:

{
    'name': 'Module',
    'start': { 'line': 0, 'ch': 0 }, 'end': { 'line': 6, 'ch': 0 },
    'children': [{
        'name': 'Expr',
        'start': { 'line': 0, 'ch': 0 }, 'end': { 'line': 5, 'ch': 1 },
        'children': [{
            'name': 'Call',
            'start': { 'line': 0, 'ch': 1 }, 'end': { 'line': 1, 'ch': 21 },
            'children': []
        }, {
            'name': 'Call',
            'start': { 'line': 0, 'ch': 1 }, 'end': { 'line': 2, 'ch': 16 },
            'children': []
        }, {
            'name': 'Subscript',
            'start': { 'line': 0, 'ch': 1 }, 'end': { 'line': 3, 'ch': 10 },
            'children': []
        }, {
            'name': 'Call',
            'start': { 'line': 0, 'ch': 1 }, 'end': { 'line': 4, 'ch': 8 },
            'children': []
        }]
    }]
}

'''

import json
import libcst as cst
import libcst.metadata as cstm
# import libcst.matchers as m


def parse(code, as_json=False):
    tree = cst.parse_module(code)
    with_meta = cstm.MetadataWrapper(tree)
    sam = NodePositions()
    _ = with_meta.visit(sam)

    return sam.root if not as_json else json.dumps(sam.root, indent=2)


def Position(pos: cstm.CodePosition):
    line = pos.line
    column = pos.column
    return {
        'line': line - 1,  # subtract 1 to match CodeMirror
        'ch': column  # ch to match CodeMirror
    }


def Node(name, start: cstm.CodeRange, end: cstm.CodeRange):
    return {
        'name': name,
        'start': Position(start),
        'end': Position(end),
        'children': [],
    }


# Assignments also attach the assign target so we know what to display when
# we preview the statement
def add_target(node, target):
    node['target'] = target
    return node


class NodePositions(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cstm.PositionProvider, )

    def __init__(self):
        # Store cst_root because we need its code_for_node method for
        # assignments
        self.cst_root = None
        self.root = None
        self.stack = []

    def visit_Module(self, node):
        self.cst_root = node
        self.root = self.make_node('Module', node)
        self.stack.append(self.root)

    # expressions contain one or more calls / subscripts
    # the tricky part is that the calls are nested in reverse order of what we
    # want to run. so the first call in df.f().g() is the function g() called
    # on df.f() . i'll flatten and reverse the chain so that the child of each
    # expr will be something like [df.f(), df.f().g()].
    def visit_Expr(self, node):
        current = self.stack[-1]
        child = self.make_node('Expr', node)
        current['children'].append(child)
        self.stack.append(child)

    def leave_Expr(self, node):
        current = self.stack[-1]
        current['children'] = list(reversed(current['children']))
        self.stack.pop()

    # Function calls, like square(2) or pd.melt(df)
    def visit_Call(self, node):
        current = self.stack[-1]
        child = self.make_node('Call', node)
        current['children'].append(child)

    # df['test'] or df[df['count'] > 10]
    def visit_Subscript(self, node):
        current = self.stack[-1]
        child = self.make_node('Subscript', node)
        current['children'].append(child)

    # Assignments, like a = 2 or df['test'] = True
    # def visit_Assign(self, node):
    #     current = self.stack[-1]
    #     child = self.make_node('Assign', node)

    #     # For df['test'], the target is just df
    #     target: cst.AssignTarget = node.targets[0]
    #     if m.matches(target.target, m.Subscript()):
    #         target = target.target.value

    #     child['target'] = self.make_node('AssignTarget', target)
    #     current['children'].append(child)
    #     self.stack.append(child)

    # def leave_Assign(self, node):
    #     self.stack.pop()

    # Don't traverse assignment target
    # def visit_AssignTarget(self, node):
    #     return False

    # def visit_Name(self, node):
    #     current = self.stack[-1]
    #     child = self.make_node('Name', node)
    #     current['children'].append(child)
    #     self.stack.append(child)

    # def leave_Name(self, node):
    #     self.stack.pop()

    # a < 2 or df.col != 0
    # def visit_Comparison(self, node):
    #     current = self.stack[-1]
    #     child = self.make_node('Comparison', node)
    #     current['children'].append(child)
    #     self.stack.append(child)

    # def leave_Comparison(self, node):
    #     self.stack.pop()

    # So that empty lines can be matched
    # def visit_TrailingWhitespace(self, node):
    #     current = self.stack[-1]
    #     child = self.make_node('TrailingWhitespace', node)
    #     current['children'].append(child)
    #     self.stack.append(child)

    # def leave_TrailingWhitespace(self, node):
    #     self.stack.pop()

    # a + 2
    # def visit_BinaryOperation(self, node):
    #     current = self.stack[-1]
    #     child = self.make_node('BinaryOperation', node)
    #     current['children'].append(child)
    #     self.stack.append(child)

    # def leave_BinaryOperation(self, node):
    #     self.stack.pop()

    # Skip comprehensions
    # TODO: visit comprehensions but don't visit their children
    def visit_ListComp(self, node):
        return False

    def visit_SetComp(self, node):
        return False

    def visit_DictComp(self, node):
        return False

    def visit_GeneratorExp(self, node):
        return False

    def positions(self, node):
        meta = self.get_metadata(cstm.PositionProvider, node)
        return meta.start, meta.end

    def make_node(self, name, node):
        start, end = self.positions(node)
        return Node(name, start, end)


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
        self.log(node, 'Call')
        self.depth += 1

    def leave_Call(self, node):
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
(df
 .sort_values('Name')
 .groupby('Sex')
 ['Count']
 .mean()
)
'''.strip()

if __name__ == "__main__":
    print(parse(test, as_json=True))
