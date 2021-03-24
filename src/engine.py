import subprocess
import os
import libadalang as lal

from src.types import Buffer
from src.project_support import ProjectResolver
from src.gui import log, GUI

# Strategies
from src.delete_empty_units import DeleteEmptyUnits
from src.hollow_body import HollowOutSubprograms
from src.remove_statement import RemoveStatements
from src.remove_subprograms import RemoveSubprograms
from src.remove_imports import RemoveImports
from src.remove_trivias import RemoveTrivias

# TODO:
#   - remove successive null statements
#   - empty bodies first
#   - use a python API for .gpr
#   - support non-gnat naming schemes?


class StrategyStats(object):
    def __init__(self, characters_removed, time):
        self.characters_removed = characters_removed
        self.time = time


class Reducer(object):
    def __init__(self, project_file, main_file, script, single_file):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)
        self.single_file = single_file
        self.overzealous_mode = False  # Whether to keep trying as long as we reduce

        self.unit_provider = lal.UnitProvider.for_project(os.path.abspath(project_file))
        self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
        self.main_file = main_file

        self.files_to_reduce = []  # Files to reduce
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

        # Prepare the list of files to reduce. First the main file...
        self.files_to_reduce.append(self.main_file)

        if self.single_file:
            self.reduce_file(self.main_file)
            return

        # ... then all the bodies
        for x in self.resolver.files:
            if x.endswith(".adb"):
                self.files_to_reduce.append(self.resolver.files[x])
        # ... then all the specs
        for x in self.resolver.files:
            if x.endswith(".ads"):
                self.files_to_reduce.append(self.resolver.files[x])

        while len(self.files_to_reduce) > 0:
            currently_reducing = self.files_to_reduce[0]
            self.files_to_reduce = self.files_to_reduce[1:]
            self.reduce_file(currently_reducing)

    def schedule(self, candidate_filename):
        """Schedule candidate_filename for reduction"""
        if (
            candidate_filename not in self.files_reduced
            and candidate_filename not in self.files_to_reduce
        ):
            self.files_to_reduce.append(candidate_filename)

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        if file in self.files_to_reduce:
            self.files_to_reduce.remove(file)

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

        if unit is None or unit.root is None:
            self.files_reduced.add(file)
            return

        # If this is a package spec, try reducing the package body first
        lib_item = unit.root.find(lal.LibraryItem)
        if lib_item is not None:
            package = lib_item.find(lal.PackageDecl)
            if package is not None:
                decl = package.children[0].p_canonical_part()
                if decl is not None:
                    body = decl.p_next_part()
                    if body is not None:
                        filename = body.unit.filename
                        if filename != file and filename not in self.files_reduced:
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
        try:
            strategy.run_on_file(self.context, file, self.run_predicate)
        except lal.PropertyError:
            # retry with a new context...
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            strategy.run_on_file(self.context, file, self.run_predicate)

        # Next remove the imports that we can remove

        log("=> Removing imports")
        strategy = RemoveImports()
        strategy.run_on_file(self.context, file, self.run_predicate)

        # Remove trivias

        log("=> Removing blank lines and comments")
        strategy = RemoveTrivias()
        strategy.run_on_file(file, self.run_predicate)

        # Attempt to delete the file if it's empty-ish

        log("=> Attempting to delete")
        strategy = DeleteEmptyUnits()
        deletion_successful = strategy.run_on_file(
            self.context, file, self.run_predicate
        )

        if deletion_successful:
            log("   File deleted! \o/")
            chars_removed = count
        else:
            buf = Buffer(file)
            chars_removed = count - buf.count_chars()

        # Print some stats

        log(f"done reducing {file} ({chars_removed} characters removed)")
        GUI.add_chars_removed(chars_removed)

        # Is this file finished?
        if self.overzealous_mode and chars_removed > 0:
            # As long as we have removed something, don't give up
            self.files_to_reduce.append(file)
        else:
            self.files_reduced.add(file)

        # Move on to the next files

        if deletion_successful:
            return

        unit = self.context.get_from_file(file, reparse=True)

        # This finds the spec/body

        lib_item = unit.root.find(lal.LibraryItem)
        if lib_item is not None:
            package = lib_item.find(lal.PackageDecl)
            if package is None:
                package = unit.root.find(lal.LibraryItem).find(lal.PackageBody)
            if package is not None:
                decl = package.children[0].p_canonical_part()
                self.schedule(decl.unit.filename)
                next = decl.p_next_part()
                while next is not None and next != decl:
                    self.schedule(next.unit.filename)
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
                    self.schedule(decl.unit.filename)
