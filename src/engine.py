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
from src.remove_generic_nodes import RemovePackages

# TODO:
#   - remove successive null statements
#   - order the .ads for processing in leaf-first mode
#   - use a python API for .gpr
#   - support non-gnat naming schemes?
#   - remove extraneous calls to predicate

# Debug convenience bits
EMPTY_OUT_BODIES_BRUTE_FORCE = False
REMOVE_PACKAGES = False
EMPTY_OUT_BODIES_STATEMENTS = False
REMOVE_SUBPROGRAMS = True
REMOVE_IMPORTS = False
REMOVE_TRIVIAS = False
ATTEMPT_DELETE = False


class StrategyStats(object):
    def __init__(self, characters_removed, time):
        self.characters_removed = characters_removed
        self.time = time


class Reducer(object):
    def __init__(self, project_file, script, single_file=None):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)
        self.single_file = single_file
        self.overzealous_mode = False  # Whether to keep trying as long as we reduce

        self.unit_provider = lal.UnitProvider.for_project(os.path.abspath(project_file))
        self.context = lal.AnalysisContext(unit_provider=self.unit_provider)

        self.bodies_to_reduce = []  # bodies to reduce
        self.ads_dict = None  # specs to reducse
        self.files_reduced = set()  # Files already reduced

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

    def sort_ads_files(self):
        """Sort .ads files into a tree structure, allowing to process
           the leaf nodes first"""

        ads_dict = {}
        # A dict showing dependencies of als
        # keys: full path to .ads files
        # values: set of files that depend on this

        # First, add them all
        for x in self.resolver.files:
            full = self.resolver.files[x]
            if full.endswith(".ads"):
                ads_dict[full] = set()

        # Now iterate on all of them
        total = len(ads_dict)
        count = 0
        for x in ads_dict:
            count += 1
            log(f"\t{count}/{total}: analyzing {x}")
            unit = self.context.get_from_file(x)

            # Iterate on all the use clauses
            root = unit.root
            if root is None:
                log(f"??? cannot find a root node for {x}")
            else:
                for w in root.findall(lambda x: x.is_a(lal.WithClause)):
                    # find the last id in w
                    ids = w.findall(lambda x: x.is_a(lal.Identifier))
                    if ids is not None:
                        id = ids[-1]
                        decl = id.p_referenced_defining_name()
                        if decl is not None:
                            if decl.unit.filename in ads_dict:
                                ads_dict[decl.unit.filename].add(x)

        self.ads_dict = ads_dict

    def mark_as_processed(self, file):
        """Mark file as processed"""

        self.files_reduced.add(file)

        if self.single_file is not None:
            return

        if file.endswith(".adb"):
            # Remove from the list of bodies
            self.bodies_to_reduce.remove(file)
        else:
            # Remove from the tree of specs
            for x in self.ads_dict:
                if file in self.ads_dict[x]:
                    self.ads_dict[x].remove(file)
            self.ads_dict.pop(file)

    def next_file_to_process(self):
        """Return the next file to process, None if we're done"""
        if len(self.bodies_to_reduce) > 0:
            return self.bodies_to_reduce[0]
        else:
            if len(self.ads_dict) == 0:
                # We're done!
                return None
            else:
                # look through all .ads files to find one on which
                # no one depends.
                for candidate in self.ads_dict:
                    if len(self.ads_dict[candidate]) == 0:
                        return candidate

                # if we reach here, there might be an issue
                log("circular dependency left over")
                return None

    def run(self):
        """Run self: reduce the project as much as possible"""

        # Before running any modification, run the predicate,
        # as a sanity check.
        if not self.run_predicate(True):
            log("The predicate returned nonzero")
            return

        # We've passed the sanity check, time to reduce!

        # Prepare the list of files to reduce. First the main file.
        if self.single_file:
            self.reduce_file(self.single_file)
            return

        # Add all the bodies
        for x in self.resolver.files:
            if x.endswith(".adb"):
                self.bodies_to_reduce.append(self.resolver.files[x])

        # Add all the specs
        self.sort_ads_files()

        candidate = self.next_file_to_process()

        while candidate is not None:
            self.reduce_file(candidate)
            candidate = self.next_file_to_process()

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        self.mark_as_processed(file)

        # Skip some cases
        if "rts-" in file:
            log(f"SKIPPING {file}: looks like a runtime file")
            return
        if not os.access(file, os.W_OK):
            log(f"SKIPPING {file}: not writable")
            return

        # Save the file to an '.orig' copy
        buf = Buffer(file)
        buf.save(file + ".orig")

        count = buf.count_chars()
        log(f"*** Reducing {file} ({count} characters)")

        unit = self.context.get_from_file(file)

        if unit is None or unit.root is None:
            return

        if EMPTY_OUT_BODIES_BRUTE_FORCE:
            log("=> Emptying out bodies (brute force)")

            strategy = HollowOutSubprograms()
            strategy.run_on_file(
                unit, buf.lines, self.run_predicate, lambda: buf.save()
            )

        # If there are bodies left, remove statements from them

        if EMPTY_OUT_BODIES_STATEMENTS:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Emptying out bodies (statement by statement)")
            buf = Buffer(file)
            unit = self.context.get_from_file(file)
            strategy = RemoveStatements()
            strategy.run_on_file(
                unit, buf.lines, self.run_predicate, lambda: buf.save()
            )

        # Remove subprograms

        if REMOVE_SUBPROGRAMS:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Removing subprograms")
            strategy = RemoveSubprograms()
            try:
                strategy.run_on_file(self.context, file, self.run_predicate)
            except lal.PropertyError:
                # retry with a new context...
                self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
                strategy.run_on_file(self.context, file, self.run_predicate)

        # Let's try removing packages

        if REMOVE_PACKAGES:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Removing packages")

            strategy = RemovePackages()
            strategy.run_on_file(self.context, file, self.run_predicate)

        # Next remove the imports that we can remove

        if REMOVE_IMPORTS:
            log("=> Removing imports")
            strategy = RemoveImports()
            strategy.run_on_file(self.context, file, self.run_predicate)

        # Remove trivias

        if REMOVE_TRIVIAS:
            log("=> Removing blank lines and comments")
            strategy = RemoveTrivias()
            strategy.run_on_file(file, self.run_predicate)

        # Attempt to delete the file if it's empty-ish

        deletion_successful = False
        if ATTEMPT_DELETE:
            log("=> Attempting to delete")
            strategy = DeleteEmptyUnits()
            deletion_successful = strategy.run_on_file(
                self.context, file, self.run_predicate
            )

        # Fin

        if deletion_successful:
            log("   File deleted! \o/")
            chars_removed = count
        else:
            buf = Buffer(file)
            chars_removed = count - buf.count_chars()

        # Print some stats

        log(f"done reducing {file} ({chars_removed} characters removed)")
        GUI.add_chars_removed(chars_removed)

        # Move on to the next files
