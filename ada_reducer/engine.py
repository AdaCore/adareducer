import subprocess
import os
import sys
import libadalang as lal

from ada_reducer.types import Buffer
from ada_reducer.project_support import ProjectResolver
from ada_reducer.gui import log, GUI

# Strategies
from ada_reducer.delete_empty_units import DeleteEmptyUnits
from ada_reducer.hollow_body import HollowOutSubprograms
from ada_reducer.remove_statement import RemoveStatements
from ada_reducer.remove_subprograms import RemoveSubprograms
from ada_reducer.remove_imports import RemoveImports
from ada_reducer.remove_trivias import RemoveTrivias
from ada_reducer.remove_generic_nodes import RemovePackages, RemoveAspects

# TODO:
#   - REMOVE .adbs in the order of .ads's
#   - remove successive null statements
#   - order the .ads for processing in leaf-first mode
#   - use a python API for .gpr
#   - support non-gnat naming schemes?
#   - remove extraneous calls to predicate

# Debug convenience bits
REMOVE_TABS = True
EMPTY_OUT_BODIES_BRUTE_FORCE = True
REMOVE_PACKAGES = True
REMOVE_ASPECTS = True
EMPTY_OUT_BODIES_STATEMENTS = True
REMOVE_SUBPROGRAMS = True
REMOVE_IMPORTS = True
REMOVE_TRIVIAS = True
ATTEMPT_DELETE = True
BRUTEFORCE_DELETE = True

# In cautious mode, run the predicate after running each file as a sanity check
CAUTIOUS_MODE = True
CAUTIOUS_MODE_HELP = """adareducer has found that the predicate no longer applies
after completing a cycle on one file. This is unexpected.

This may happen when the predicate uses a builder which looks at
timestamps in order to check whether a file needs rebuilding: if
the modifications happen faster than the granularity of the
filesystem timestamps, this will fool this check.

If you are using "gprbuild" in your predicate, make sure to pass "-m2".
"""


class StrategyStats(object):
    def __init__(self, characters_removed, time):
        self.characters_removed = characters_removed
        self.time = time


class Reducer(object):
    def __init__(self, project_file, script, single_file=None, follow_closure=False):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)
        self.single_file = single_file
        self.follow_closure = follow_closure
        self.overzealous_mode = False  # Whether to keep trying as long as we reduce

        self.unit_provider = lal.UnitProvider.for_project(os.path.abspath(project_file))
        self.context = lal.AnalysisContext(unit_provider=self.unit_provider)

        self.mains_to_reduce = set()
        self.bodies_to_reduce = []  # bodies to reduce
        self.ads_dict = {}  # specs to reduce
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

    def attempt_delete_all(self, files):
        """attempt pretend-deletion of all files in files by appending
        '.deleted' to the file name
        """

        def pretend_deletion(name):
            return f"{file}.deleted"

        for file in files:
            os.rename(file, pretend_deletion(file))
        if not self.run_predicate():
            for file in files:
                os.rename(pretend_deletion(file), file)
            if len(files) > 1:
                self.attempt_delete_all(files[: len(files) // 2])
                self.attempt_delete_all(files[len(files) // 2 :])

    def attempt_delete(self, file):
        """attempt deletion of f"""
        buf = Buffer(file)
        os.remove(file)
        if self.run_predicate():
            log("... yay, deleted \o/")
        else:
            # put the file back
            buf.save()
            log("... didn't work.")

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
                self.attempt_delete(x)
            else:
                for w in root.findall(lambda x: x.is_a(lal.WithClause)):
                    if not w.children[0].is_a(lal.LimitedPresent):
                        # find the last id in w
                        ids = w.findall(lambda x: x.is_a(lal.Identifier))
                        if ids is not None:
                            id = ids[-1]
                            decl = id.p_referenced_defining_name()
                            if decl is not None:
                                if decl.unit.filename in ads_dict:
                                    ads_dict[decl.unit.filename].add(x)

        self.ads_dict = ads_dict

        # Find all bodies that are mains, so we can process them first.
        # TODO: migrate this to the gpr2 API when it exists.
        # Until then, duct tape:
        for x in self.bodies_to_reduce:
            spec = x[:-1] + "s"
            if spec not in self.ads_dict:
                self.mains_to_reduce.add(x)

    def mark_as_processed(self, file):
        """Mark file as processed"""

        self.files_reduced.add(file)

        if file.endswith(".adb"):
            if file in self.mains_to_reduce:
                self.mains_to_reduce.remove(file)

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
        if len(self.mains_to_reduce) > 0:
            return self.mains_to_reduce.pop()

        if len(self.ads_dict) == 0:
            if len(self.bodies_to_reduce) == 0:
                # We're done!
                return None
            else:
                return self.bodies_to_reduce[0]
        else:
            # look through all .ads files to find one on which
            # no one depends.
            for candidate in self.ads_dict:
                if len(self.ads_dict[candidate]) == 0:
                    # find the body corresponding to this candidate
                    bod = candidate[:-1] + "b"
                    if bod in self.bodies_to_reduce:
                        return bod
                    return candidate
            # if we reach here, there might be an issue
            log("circular dependency left over")
            for c in self.ads_dict:
                print(c)
                for dep in self.ads_dict[c]:
                    print(f"    {dep}")

            return None

    def run(self):
        """Run self: reduce the project as much as possible"""

        # Before running any modification, run the predicate,
        # as a sanity check.
        if not self.run_predicate(True):
            log("The predicate returned nonzero")
            return

        # We've passed the sanity check, time to reduce!

        # Attempt to remove all files in the project before doing any
        # reduction: this might save time by deleting files we would have tried
        # to reduce.
        if BRUTEFORCE_DELETE:
            self.attempt_delete_all(
                [self.resolver.files[name] for name in self.resolver.files]
            )

        # Prepare the list of files to reduce. First the main file.
        if self.single_file:
            candidate = self.single_file

            # Only add the single file
            if candidate.endswith(".adb"):
                self.bodies_to_reduce.append(candidate)
            else:
                self.ads_dict[candidate] = []
            candidate = self.single_file
        else:

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

    def apply_strategies_on_file(self, file, buf) -> int:
        """Apply all the strategies on the given buf.

        Return the number of characters removed.
        """
        count = buf.count_chars()

        if REMOVE_TABS:
            log("=> Removing tabs")
            buf.strip_tabs()
            if CAUTIOUS_MODE and buf.count_chars() < count:
                # In cautious mode, if we actually did
                # remove some tabs, run the predicate as a check.
                if not self.run_predicate():
                    log(f"The issue is gone after stripping TABs in {file}")
                    log("adareducer cannot help in this case.")
                    sys.exit(1)

        unit = self.context.get_from_file(file)

        if unit is None or unit.root is None:
            log(f"??? cannot find a root node for {file}")
            self.attempt_delete(file)
            return 0


        if EMPTY_OUT_BODIES_BRUTE_FORCE:
            log("=> Emptying out bodies (brute force)")

            HollowOutSubprograms().run_on_file(
                unit, buf.lines, self.run_predicate, lambda: buf.save()
            )

        # If there are bodies left, remove statements from them

        if EMPTY_OUT_BODIES_STATEMENTS:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Emptying out bodies (statement by statement)")
            buf = Buffer(file)
            unit = self.context.get_from_file(file)
            RemoveStatements().run_on_file(
                unit, buf.lines, self.run_predicate, lambda: buf.save()
            )

        # Let's try removing aspects

        if REMOVE_ASPECTS:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Removing aspects")
            RemoveAspects().run_on_file(self.context, file, self.run_predicate)

        # Remove subprograms

        if REMOVE_SUBPROGRAMS:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Removing subprograms")
            try:
                RemoveSubprograms().run_on_file(self.context, file, self.run_predicate)
            except lal.PropertyError:
                # retry with a new context...
                self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
                RemoveSubprograms().run_on_file(self.context, file, self.run_predicate)

        # Let's try removing packages

        if REMOVE_PACKAGES:
            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            log("=> Removing packages")
            RemovePackages().run_on_file(self.context, file, self.run_predicate)

        # Next remove the imports that we can remove

        if REMOVE_IMPORTS:
            log("=> Removing imports")
            RemoveImports().run_on_file(self.context, file, self.run_predicate)

        # Remove trivias

        if REMOVE_TRIVIAS:
            log("=> Removing blank lines and comments")
            RemoveTrivias().run_on_file(file, self.run_predicate)

        # Attempt to delete the file if it's empty-ish

        deletion_successful = False
        if ATTEMPT_DELETE:
            log("=> Attempting to delete")
            deletion_successful = DeleteEmptyUnits().run_on_file(
                self.context, file, self.run_predicate
            )

        # Fin

        if deletion_successful:
            log("   File deleted! \o/")
            chars_removed = count
        else:
            buf = Buffer(file)
            chars_removed = count - buf.count_chars()

        return chars_removed

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

        log(f"*** Reducing {file}")

        # Save the file to an '.orig' copy
        buf = Buffer(file)
        buf.save(file + ".orig")

        try:
            chars_removed = self.apply_strategies_on_file(file, buf)
        except:
            # Catch any exception occurring during the application of
            # strategies, and save the buf to a .crash file, to
            # help post-mortem analysis.
            chars_removed = 0
            buf.save(file + ".crash")
            raise

        # Print some stats

        log(f"done reducing {file} ({chars_removed} characters removed)")
        GUI.add_chars_removed(chars_removed)

        # Cautious?

        if CAUTIOUS_MODE:
            if not self.run_predicate():
                log(CAUTIOUS_MODE_HELP)
                sys.exit(1)

        # Move on to the next files

        if self.follow_closure:
            # First let's check if we are processing a .adb that has a .ads
            if file.endswith(".adb"):
                ads = file[:-1] + "s"
                if os.path.exists(ads):
                    # this exists, it's the natural next one to check
                    self.ads_dict[ads] = []
                    return

            self.context = lal.AnalysisContext(unit_provider=self.unit_provider)
            unit = self.context.get_from_file(file)
            root = unit.root
            if root is not None:
                # Iterate through all "with" statements
                for w in root.findall(lambda x: x.is_a(lal.WithClause)):
                    # find the last id in w
                    ids = w.findall(lambda x: x.is_a(lal.Identifier))
                    if ids is not None:
                        id = ids[-1]
                        decl = id.p_referenced_defining_name()
                        # find the definition
                        if decl is not None:
                            file_to_add = decl.unit.filename

                            # Only process files that are in the project closure
                            if self.resolver.belongs_to_project(file_to_add):
                                if file_to_add.endswith(".ads"):
                                    # if it's a .ads we want to empty, empty
                                    # the .adb first, it will go faster
                                    adb = file_to_add[:-1] + "b"
                                    if os.path.exists(adb):
                                        self.bodies_to_reduce.append(adb)
                                    self.ads_dict[file_to_add] = []
                                else:
                                    self.bodies_to_reduce.append(file_to_add)
