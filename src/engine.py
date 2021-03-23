import subprocess
import os
import libadalang as lal
from src.types import Buffer
from src.project_support import ProjectResolver
from src.gui import log, GUI

# Strategies
from src.hollow_body import HollowOutSubprograms
from src.remove_statement import RemoveStatements
from src.remove_subprograms import RemoveSubprograms
from src.remove_imports import RemoveImports
from src.remove_trivias import RemoveTrivias

# TODO:
#   - remove successive null statements
#   - empty bodies first
#   - remove body files when they are empty
#   - transform "to reduce" set in a round robin ordered list


class StrategyStats(object):
    def __init__(self, characters_removed, time):
        self.characters_removed = characters_removed
        self.time = time


class Reducer(object):
    def __init__(self, project_file, main_file, script):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)

        unit_provider = lal.UnitProvider.for_project(os.path.abspath(project_file))
        self.context = lal.AnalysisContext(unit_provider=unit_provider)
        self.main_file = main_file

        self.files_to_reduce = set()  # Files to reduce
        self.files_reduced = set()  # Files already reduced

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

        self.files_to_reduce.add(self.main_file)

        while len(self.files_to_reduce) > 0:
            currently_reducing = self.files_to_reduce.pop()
            self.reduce_file(currently_reducing)

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        # Skip some cases
        if "rts-" in file:
            log(f"SKIPPING {file}: looks like a runtime file")
            self.files_reduced.add(file)
            return
        if not os.access(file, os.W_OK):
            log(f"SKIPPING {file}: not writable")
            self.files_reduced.add(file)
            return

        # Save the file to an '.orig' copy
        buf = Buffer(file)
        buf.save(file + ".orig")

        count = buf.count_chars()
        log(f"*** Reducing {file} ({count} characters)")

        unit = self.context.get_from_file(file)

        # If this is a package spec, try reducing the package body first
        package = unit.root.find(lal.LibraryItem).find(lal.PackageDecl)
        if package is not None:
            decl = package.children[0].p_canonical_part()
            if decl is not None:
                body = decl.p_next_part()
                if body is not None:
                    filename = body.unit.filename
                    if filename not in self.files_reduced:
                        log("=> Reducing the body first")
                        self.reduce_file(filename)

        def predicate():
            buf.save()
            return self.run_predicate()

        log("=> Emptying out bodies (brute force)")

        strategy = HollowOutSubprograms()
        strategy.run_on_file(unit, buf.lines, predicate)

        # If there are bodies left, remove statements from them

        log("=> Emptying out bodies (statement by statement)")

        unit = self.context.get_from_file(file, reparse=True)
        strategy = RemoveStatements()
        strategy.run_on_file(unit, buf.lines, predicate)

        # Remove subprograms

        log("=> Removing subprograms")

        strategy = RemoveSubprograms()
        strategy.run_on_file(self.context, file, self.run_predicate)

        # Next remove the imports that we can remove

        log("=> Removing imports")

        strategy = RemoveImports()
        strategy.run_on_file(self.context, file, self.run_predicate)

        # Remove trivias

        log("=> Removing blank lines and comments")
        strategy = RemoveTrivias()
        strategy.run_on_file(file, self.run_predicate)

        # Print some stats

        buf = Buffer(file)
        chars_removed = count - buf.count_chars()
        GUI.add_chars_removed(chars_removed)
        log(f"done reducing {file} ({chars_removed} characters removed)")

        # Is this file finished?
        # As long as we have removed something, don't give up
        if chars_removed > 0:
            self.files_to_reduce.add(file)
        else:
            self.files_reduced.add(file)

        # Move on to the next files

        unit = self.context.get_from_file(file, reparse=True)

        # This finds the spec/body
        package = unit.root.find(lal.LibraryItem).find(lal.PackageDecl)
        if package is None:
            package = unit.root.find(lal.LibraryItem).find(lal.PackageBody)
        if package is not None:
            decl = package.children[0].p_canonical_part()
            candidate_filename = decl.unit.filename
            if candidate_filename not in self.files_reduced:
                self.files_to_reduce.add(candidate_filename)
            next = decl.p_next_part()
            while next is not None and next != decl:
                candidate_filename = next.unit.filename
                if candidate_filename not in self.files_reduced:
                    self.files_to_reduce.add(candidate_filename)
                decl = next
                next = next.p_next_part()

        # This finds all imported packages
        for w in unit.root.findall(lambda x: x.is_a(lal.WithClause)):
            # find the last id in w
            ids = w.findall(lambda x: x.is_a(lal.Identifier))
            if ids is not None:
                id = ids[-1]
                decl = id.p_referenced_defining_name()
                if decl is not None:
                    candidate_filename = decl.unit.filename
                    if candidate_filename not in self.files_reduced:
                        self.files_to_reduce.add(candidate_filename)
