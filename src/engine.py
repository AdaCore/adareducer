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
        buf = Buffer(file)
        buf.save(file + ".orig")

        count = buf.count_chars()
        log(f"*** Reducing {file} ({count} characters)")

        def predicate():
            buf.save()
            return self.run_predicate()

        log("=> Emptying out bodies (brute force)")

        unit = self.context.get_from_file(file)

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

        # TODO

        # Move on to other files to reduce

        # TODO

        buf = Buffer(file)
        chars_removed = count - buf.count_chars()
        GUI.add_chars_removed(chars_removed)
        log(f"done reducing {file} ({chars_removed} characters removed)")
        # TODO: after reducing the file, reduce its dependencies
