import subprocess
import os
import libadalang as lal
from src.types import replace, read_file, write_file, count_chars
from src.project_support import ProjectResolver
from src.interfaces import ChunkInterface, StrategyInterface
from src.dichotomy import dichotomize, to_tree, dichototree
from src.gui import log, GUI


class StrategyStats(object):
    def __init__(self, characters_removed, time):
        self.characters_removed = characters_removed
        self.time = time


class HollowBody(ChunkInterface):
    def __init__(self, unit, lines, node):
        """node is a lal.SubpBody. Hollow it out."""
        self.unit = unit
        self.lines = lines
        self.node = node

        self.spec = self.node.find(lal.SubpSpec)
        self.decl = self.node.find(lal.DeclarativePart).find(lal.AdaNodeList)
        self.statements = self.node.find(lal.HandledStmts).find(lal.StmtList)

        self.statements_lines = None
        self.statements_range = None
        self.decl_range = None
        self.decl_lines = None

    def do(self):
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
        def infer_or_equal(a, b):
            if a.line < b.line:
                return True
            elif a.line > b.line:
                return False
            else:
                return a.column <= b.column

        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class HollowOutSubprograms(StrategyInterface):
    """The goal of this strategy is to hollow out the
       body of subprograms as much as possible
    """

    def run_on_file(self, unit, lines, predicate):

        # Create some chunks of work
        chunks = []

        for subp in unit.root.findall(lambda x: x.is_a(lal.SubpBody)):
            # Hollow out the bodies
            chunks.append(HollowBody(unit, lines, subp))

        # Order the chunks to make sure that nesting edits don't block each other
        chunks.sort(key=lambda c: c.decl.sloc_range.start.line)

        t = to_tree(chunks)
        return dichototree(t, predicate)


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
        def infer_or_equal(a, b):
            if a.line < b.line:
                return True
            elif a.line > b.line:
                return False
            else:
                return a.column <= b.column

        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class RemoveStatements(StrategyInterface):
    """This strategy removes statements from bodies of subprograms"""

    def run_on_file(self, unit, lines, predicate):
        """subps_to_try contains the list of subp nodes to try"""

        chunks = []
        for subp in unit.root.findall(lambda x: x.is_a(lal.SubpBody)):
            # Find all statement lists
            stmtlists = subp.findall(lambda x: x.is_a(lal.StmtList))
            for stmtlist in stmtlists:
                children = stmtlist.children
                for stmt in children:
                    chunks.append(
                        RemoveStatement(stmt, lines, is_lone=len(children) <= 1)
                    )

        # Order the chunks
        chunks.sort(key=lambda c: c.node.sloc_range.start.line)

        t = to_tree(chunks)

        # Do the work
        return dichototree(t, predicate)


class Reducer(object):
    def __init__(self, project_file, main_file, script):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)

        unit_provider = lal.UnitProvider.for_project(os.path.abspath(project_file))
        self.context = lal.AnalysisContext(unit_provider=unit_provider)
        self.main_file = main_file
        if not os.path.isabs(main_file):
            self.main_file = self.resolver.find(main_file)

    def run_predicate(self, print_if_error=False):
        """Run predicate and return True iff predicate returned 0."""
        if self.script.endswith(".sh"):
            cmd = ["bash", self.script]
        else:
            cmd = [self.script]

        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = out.returncode == 0
        if print_if_error and not status:
            log(out.stdout.decode() + "\n" + out.stderr.decode())
        return status

    def run(self):
        """Run self: reduce the project as much as possible"""

        # Before running any modification, run the predicate,
        # as a sanity check.
        if not self.run_predicate(True):
            log("The predicate returned nonzero")
            return

        # We've passed the sanity check, time to reduce!
        self.reduce_file(self.main_file)

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        # Save the file to an '.orig' copy
        lines = read_file(file)
        write_file(file + ".orig", lines)

        count = count_chars(lines)
        log(f"reducing {file} ({count} characters)")

        # First remove the bodies of procedures

        unit = self.context.get_from_file(file)

        def predicate():
            write_file(file, lines)
            return self.run_predicate()

        strategy = HollowOutSubprograms()
        strategy.run_on_file(unit, lines, predicate)

        # If there are bodies left, remove statements from them

        unit = self.context.get_from_file(file, reparse=True)
        strategy = RemoveStatements()
        strategy.run_on_file(unit, lines, predicate)

        # Remove subprograms

        # TODO

        # Next remove the imports that we can remove

        # TODO

        # Move on to other files to redude

        # TODO

        write_file(file, lines)
        chars_removed = count - count_chars(lines)
        GUI.add_chars_removed(chars_removed)
        log(f"done reducing {file} ({chars_removed} characters removed)")
        # TODO: after reducing the file, reduce its dependencies
