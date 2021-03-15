import subprocess
import os


class ProjectResolver(object):
    """Utility to resolve base names"""

    def __init__(self, project_file):
        self.files = {}

        # Use gprls to find the list of files in the project
        # TODO: replace this whole thing with the python gpr2 API

        out = subprocess.run(
            ["gprls", "-P", project_file, "-s"], stdout=subprocess.PIPE
        )
        file_list = out.stdout.splitlines()
        for f in file_list:
            self.files[os.path.basename(f).decode()] = f.decode()

    def find(self, basename):
        """Return full path to file named basename in project, None if not found"""
        if not basename in self.files:
            print(f"file {basename} not found in project")
            return None
        return self.files[basename]
