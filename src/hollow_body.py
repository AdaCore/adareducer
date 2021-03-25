import libadalang as lal
from src.types import replace, infer_or_equal
from src.interfaces import ChunkInterface, StrategyInterface
from src.dichotomy import to_tree, dichototree


class HollowBody(ChunkInterface):
    def __init__(self, unit, lines, node):
        """node is a lal.SubpBody. Hollow it out."""
        self.unit = unit
        self.lines = lines
        self.node = node

        self.spec = self.node.find(lal.SubpSpec)
        self.decl = self.node.find(lal.DeclarativePart).find(lal.AdaNodeList)
        handled = self.node.find(lal.HandledStmts)
        if handled is not None:
            self.statements = handled.find(lal.StmtList)
        else:
            self.statements = None

        self.statements_lines = None
        self.statements_range = None
        self.decl_range = None
        self.decl_lines = None

    def do(self):
        if not self.statements:
            return
        is_procedure = self.spec.children[0].is_a(lal.SubpKindProcedure)
        if is_procedure:
            # For procedures, we replace the body with a "null;" statement
            # plus
            body_replacement = ["null;"]
        else:
            # For functions, we need to craft a "return" statement to preserve
            # compilability
            self_name = self.node.find(lal.DefiningName).text
            params = self.spec.find(lal.ParamSpecList)
            if params:
                pms = []
                for j in params.children:
                    pms.append(j.find(lal.DefiningName).text)
                param_words = ", ".join(pms)
                body_replacement = [f"return {self_name} ({param_words});"]
            else:
                body_replacement = [f"return {self_name};"]

        # Add enough empty lines to preserve line numbers
        body_replacement += [""] * (
            self.statements.sloc_range.end.line - self.statements.sloc_range.start.line
        )

        # Replace the body
        self.statements_range, self.statements_lines = replace(
            self.lines, self.statements.sloc_range, body_replacement
        )

        # Replace the declarative part if it's non-empty
        if self.decl.sloc_range.end.line != self.decl.sloc_range.start.line:
            self.decl_range, self.decl_lines = replace(
                self.lines,
                self.decl.sloc_range,
                [""]
                * (self.decl.sloc_range.end.line - self.decl.sloc_range.start.line + 1),
            )

    def undo(self):
        if self.decl_range is not None:
            _, l = replace(self.lines, self.decl_range, self.decl_lines)
        if self.statements_range is not None:
            replace(self.lines, self.statements_range, self.statements_lines)

    def is_in(self, other):
        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class HollowOutSubprograms(StrategyInterface):
    """The goal of this strategy is to hollow out the
       body of subprograms as much as possible
    """

    def run_on_file(self, unit, lines, predicate, save):

        # Create some chunks of work
        chunks = []

        for subp in unit.root.findall(lambda x: x.is_a(lal.SubpBody)):
            # Hollow out the bodies
            chunks.append(HollowBody(unit, lines, subp))

        # Order the chunks to make sure that nesting edits don't block each other
        chunks.sort(key=lambda c: c.decl.sloc_range.start.line)

        t = to_tree(chunks)
        return dichototree(t, predicate, save)
