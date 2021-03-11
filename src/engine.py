import subprocess
import os
import libadalang as lal

class ProjectResolver(object):
    """Utility to resolve base names"""

    def __init__(self, project_file):
        self.files = {}

        # Use gprls to find the list of files in the project
        # TODO: replace this whole thing with the python gpr2 API

        out = subprocess.run(["gprls", "-P", project_file, "-s"], stdout=subprocess.PIPE)
        file_list = out.stdout.splitlines()
        for f in file_list:
            self.files[os.path.basename(f).decode()] = f.decode()

    def find(self, basename):
        """Return full path to file named basename in project, None if not found"""
        if not basename in self.files:
            print(f"file {basename} not found in project")
            return None
        return self.files[basename]


class Reducer(object):

    def __init__(self, project_file, main_file, script):
        self.project_file = project_file
        self.script = script
        self.resolver = ProjectResolver(project_file)
        self.main_file = main_file
        if not os.path.isabs(main_file):
            self.main_file = self.resolver.find(main_file)

    def run_predicate(self):
        """Run predicate and return True iff predicate returned 0"""
        if self.script.endswith(".sh"):
            cmd = ["bash", self.script]
        else:
            cmd = [self.script]

        out = subprocess.run(cmd)
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

    def read_file(self, file):
        """ Return the contents of file as an array of lines, with 
            an extra empty one at the top so that line numbers correspond
            to indexes
        """
        with open(file, "rb") as f:
            return [None] + f.read().decode().splitlines()

    def write_file(self, file, lines):
        """ Write buffer to file from its line array, popping the one at first"""
        with open(file, "wb") as f:
            f.write("\n".join(lines[1:]).encode() + "\n")

    def remove_procedure_bodies(self, file, unit, lines):
        """Hollow out the bodies of procedures"""

        # list all the procedures


        return buffer

    def reduce_file(self, file):
        """Reduce one given file as much as possible"""

        print(f"reducing {file}...")

        # TODO: save the file to an '.orig' copy

        lines = self.read_file(file)
        self.write_file(file + ".orig", lines)

        unit = 

        # TODO: remove stuff

        # First remove the bodies of procedures

        self.remove_procedure_bodies(file)

        print(f"done reducing {file}")
        # TODO: after reducing the file, reduce its dependencies