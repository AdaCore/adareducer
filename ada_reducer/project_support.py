import os
import libadalang as lal
from pathlib import PurePath


class ProjectResolver(object):
    """Utility to resolve base names"""

    def __init__(self, project_file):
        self.files = {}
        # The sources in this project tree, not including externally built
        # projects.
        # Keys: base names, values: full names

        # Use the Libadalang API to query the sources for this project.
        # This collects the sources in all the project tree, not including
        # sources in externally built projects.
        #
        # TODO: It may be necessary to pass scenario variables, target and
        # runtime name information here in order for the project file to load
        # correctly.
        gpr = lal.GPRProject(project_file)
        files = gpr.source_files()

        for full_path in files:
            basename = PurePath(full_path).name
            # For ad-hoc projects in particular, compilation artifacts
            # of the form b__* might find themselves in source dirs:
            # ignore them.
            if not basename.startswith("b__"):
                # This could happen in the case of aggregate projects: warn
                assert (
                    not basename in self.files
                ), f"{basename} is present twice in sources - use non-aggregate project"

                self.files[basename] = str(full_path)

    def find(self, basename):
        """Return full path to file named basename in project, None if not found"""
        if not basename in self.files:
            print(f"file {basename} not found in project")
            return None
        return self.files[basename]

    def belongs_to_project(self, filename):
        """Return True iff filename is a source of this project tree,
        not including externally built projects.
        """
        basename = PurePath(filename).name
        return basename in self.files
