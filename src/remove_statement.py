import libadalang as lal
from src.types import replace, infer_or_equal
from src.interfaces import ChunkInterface, StrategyInterface
from src.dichotomy import to_tree, dichototree


class RemoveStatement(ChunkInterface):
    def __init__(self, node, lines, is_lone):
        self.node = node
        self.is_lone = is_lone
        self.lines = lines

    def do(self):
        num_lines = self.node.sloc_range.end.line - self.node.sloc_range.start.line + 1
        new_text = ["null;"] + [""] * (num_lines - 1)
        self.range, self.new_lines = replace(self.lines, self.node.sloc_range, new_text)

    def undo(self):
        replace(self.lines, self.range, self.new_lines)

    def __str__(self):
        return f"remove {self.node.sloc_range}"

    def is_in(self, other):
        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class RemoveDecl(ChunkInterface):
    def __init__(self, node, lines, is_lone):
        self.node = node
        self.is_lone = is_lone
        self.lines = lines

    def do(self):
        num_lines = self.node.sloc_range.end.line - self.node.sloc_range.start.line + 1
        new_text = [""] * (num_lines)
        self.range, self.new_lines = replace(self.lines, self.node.sloc_range, new_text)

    def undo(self):
        replace(self.lines, self.range, self.new_lines)

    def __str__(self):
        return f"remove {self.node.sloc_range}"

    def is_in(self, other):
        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class RemoveStatements(StrategyInterface):
    """This strategy removes statements from bodies of subprograms"""

    def run_on_file(self, unit, lines, predicate, save):
        """subps_to_try contains the list of subp nodes to try"""

        chunks = []
        # Find all statement lists and decl lists
        if unit.root is None:
            return
        for stmtlist in unit.root.findall(lambda x: x.is_a(lal.StmtList)):
            children = stmtlist.children
            for stmt in children:
                chunks.append(RemoveStatement(stmt, lines, is_lone=len(children) <= 1))
        for stmtlist in unit.root.findall(
            lambda x: x.is_a(lal.DeclList) or x.is_a(lal.AdaNodeList)
        ):
            children = stmtlist.children
            for stmt in children:
                chunks.append(RemoveDecl(stmt, lines, is_lone=len(children) <= 1))

        # Order the chunks
        chunks.sort(key=lambda c: c.node.sloc_range.start.line)

        t = to_tree(chunks)

        # Do the work
        return dichototree(t, predicate, save)
