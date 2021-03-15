import subprocess
import os
import libadalang as lal
from src.types import replace, read_file, write_file
from src.project_support import ProjectResolver
from src.interfaces import ChunkInterface, StrategyInterface
from src.dichotomy import dichotomize


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
        self.statements_lines = None
        self.statements_range = None
        self.decl_range = None
        self.decl_lines = None

    def do(self):
        spec = self.node.find(lal.SubpSpec)
        is_procedure = spec.children[0].is_a(lal.SubpKindProcedure)

        decl = self.node.find(lal.DeclarativePart).find(lal.AdaNodeList)
        statements = self.node.find(lal.HandledStmts).find(lal.StmtList)

        if is_procedure:
            # For procedures, we replace the body with a "null;" statement
            # plus
            body_replacement = ["null;"]
        else:
            # For functions, we need to craft a "return" statement to preserve
            # compilability
            self_name = self.node.find(lal.DefiningName).text
            params = spec.find(lal.ParamSpecList)
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
            statements.sloc_range.end.line - statements.sloc_range.start.line
        )

        # Replace the body
        self.statements_range, self.statements_lines = replace(
            self.lines, statements.sloc_range, body_replacement
        )

        # Replace the declarative part if it's non-empty
        if decl.sloc_range.end.line != decl.sloc_range.start.line:
            self.decl_range, self.decl_lines = replace(
                self.lines,
                decl.sloc_range,
                [""] * (decl.sloc_range.end.line - decl.sloc_range.start.line + 1),
            )

    def undo(self):
        if self.decl_range is not None:
            _, l = replace(self.lines, self.decl_range, self.decl_lines)
        if self.statements_range is not None:
            replace(self.lines, self.statements_range, self.statements_lines)


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

        not_processed = dichotomize(chunks, predicate)
        return not_processed


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

    def run_predicate(self):
        """Run predicate and return True iff predicate returned 0"""
        if self.script.endswith(".sh"):
            cmd = ["bash", self.script]
        else:
            cmd = [self.script]

        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return out.returncode == 0

    def run(self):
        """Run self: reduce the project as much as possible"""

        # Before running any modification, run the predicate,
        # as a sanity check.
        if not self.run_predicate():
            print("The predicate returned nonzero")
            return

        # We've passed the sanity check, time to reduce!
        self.reduce_file(self.main_file)

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        print(f"reducing {file}...")

        # Save the file to an '.orig' copy

        lines = read_file(file)
        write_file(file + ".orig", lines)

        # First remove the bodies of procedures

        unit = self.context.get_from_file(file)

        def predicate():
            write_file(file, lines)
            return self.run_predicate()

        strategy = HollowOutSubprograms()
        strategy.run_on_file(unit, lines, predicate)

        write_file(file, lines)
        print(f"done reducing {file}")
        # TODO: after reducing the file, reduce its dependencies
