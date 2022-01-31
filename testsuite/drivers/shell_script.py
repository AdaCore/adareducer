from drivers.base_driver import BaseDriver
import os
import shutil


class ShellScriptDriver(BaseDriver):
    """
    Driver to run a sh script.

    Interface:

    * put a "test.sh" script in the test directory;
    * put a "test.out" text file in the test directory,
      with expected results. A missing test.out is treated
      as empty.

    This driver will run the sh script. Its output is then checked against
    the expected output (test.out file). Use this driver only for legacy tests.
    """

    @property
    def default_process_timeout(self):
        return 300

    def run(self):

        test_name = os.path.split(self.test_dir())[-1]

        p = self.shell(["bash", "test.sh"], catch_error=False)

        if p.status:
            self.output += ">>>program returned status code {}\n".format(p.status)
